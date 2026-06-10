#include "renderer/chaos_field.h"
#include "util/log.h"

#include <glad/gl.h>
#include <cuda_runtime.h>
#include <cuda_gl_interop.h>

#include <vector>

namespace astra_viz {

namespace {
bool ok(cudaError_t e, const char* op) {
    if (e == cudaSuccess) return true;
    astra_viz::log::error("CUDA %s: %s", op, cudaGetErrorString(e));
    return false;
}
} // anon

bool ChaosField::create_texture(int idx) {
    glGenTextures(1, &gl_tex_[idx]);
    glBindTexture(GL_TEXTURE_3D, gl_tex_[idx]);
    glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE);
    std::vector<float> zeros((size_t)resolution_ * resolution_ * resolution_, 0.0f);
    glTexImage3D(GL_TEXTURE_3D, 0, GL_R32F, resolution_, resolution_, resolution_,
                 0, GL_RED, GL_FLOAT, zeros.data());
    glBindTexture(GL_TEXTURE_3D, 0);
    return ok(cudaGraphicsGLRegisterImage(&cuda_res_[idx], gl_tex_[idx], GL_TEXTURE_3D,
                                           cudaGraphicsRegisterFlagsSurfaceLoadStore),
              "cudaGraphicsGLRegisterImage(chaos)");
}

bool ChaosField::init(int resolution, float world_half_extent) {
    resolution_ = resolution;
    world_half_extent_ = world_half_extent;

    if (!create_texture(0)) return false;
    if (!create_texture(1)) return false;

    glGenVertexArrays(1, &vao_);

    const std::string& root = astra_viz::exe_directory();
    if (!raymarch_prog_.load_from_files(root + "shaders/chaos_field/raymarch.vert",
                                         root + "shaders/chaos_field/raymarch.frag")) {
        astra_viz::log::error("chaos_field raymarch program load failed");
        return false;
    }

    astra_viz::log::info("ChaosField: 2x %d^3 GL_R32F (ping-pong, half-extent %.1f m)",
                         resolution_, world_half_extent_);
    return true;
}

void ChaosField::seed(float amp, float sigma_voxels) {
    cudaError_t e = cudaGraphicsMapResources(1, &cuda_res_[current_], 0);
    if (e != cudaSuccess) { ok(e, "MapResources(seed)"); return; }
    cudaArray_t arr;
    e = cudaGraphicsSubResourceGetMappedArray(&arr, cuda_res_[current_], 0, 0);
    if (!ok(e, "GetMappedArray(seed)")) {
        cudaGraphicsUnmapResources(1, &cuda_res_[current_], 0);
        return;
    }
    cudaResourceDesc rd = {};
    rd.resType = cudaResourceTypeArray;
    rd.res.array.array = arr;
    cudaSurfaceObject_t surf = 0;
    if (ok(cudaCreateSurfaceObject(&surf, &rd), "CreateSurfaceObject(seed)")) {
        ok(launch_chaos_seed_kernel(surf, resolution_, amp, sigma_voxels), "seed_kernel");
        cudaDestroySurfaceObject(surf);
    }
    cudaGraphicsUnmapResources(1, &cuda_res_[current_], 0);
}

void ChaosField::step(const ChaosPDEParams& p) {
    int read_idx  = current_;
    int write_idx = 1 - current_;
    cudaGraphicsResource* res[2] = { cuda_res_[read_idx], cuda_res_[write_idx] };

    if (!ok(cudaGraphicsMapResources(2, res, 0), "MapResources(step)")) return;

    cudaArray_t arr_r = nullptr, arr_w = nullptr;
    if (!ok(cudaGraphicsSubResourceGetMappedArray(&arr_r, res[0], 0, 0), "GetMappedArray(read)") ||
        !ok(cudaGraphicsSubResourceGetMappedArray(&arr_w, res[1], 0, 0), "GetMappedArray(write)")) {
        cudaGraphicsUnmapResources(2, res, 0);
        return;
    }

    cudaResourceDesc rd{};
    rd.resType = cudaResourceTypeArray;
    rd.res.array.array = arr_r;
    cudaSurfaceObject_t surf_r = 0;
    cudaCreateSurfaceObject(&surf_r, &rd);
    rd.res.array.array = arr_w;
    cudaSurfaceObject_t surf_w = 0;
    cudaCreateSurfaceObject(&surf_w, &rd);

    ok(launch_chaos_pde_step(surf_r, surf_w, resolution_, p), "chaos_pde");

    cudaDestroySurfaceObject(surf_r);
    cudaDestroySurfaceObject(surf_w);
    cudaGraphicsUnmapResources(2, res, 0);

    current_ = write_idx;
}

void ChaosField::clear() {
    for (int i = 0; i < 2; i++) {
        if (!ok(cudaGraphicsMapResources(1, &cuda_res_[i], 0), "MapResources(clear)")) continue;
        cudaArray_t arr;
        if (ok(cudaGraphicsSubResourceGetMappedArray(&arr, cuda_res_[i], 0, 0), "GetMappedArray(clear)")) {
            cudaResourceDesc rd = {};
            rd.resType = cudaResourceTypeArray;
            rd.res.array.array = arr;
            cudaSurfaceObject_t s = 0;
            if (ok(cudaCreateSurfaceObject(&s, &rd), "CreateSurfaceObject(clear)")) {
                ok(launch_chaos_clear_kernel(s, resolution_), "clear_kernel");
                cudaDestroySurfaceObject(s);
            }
        }
        cudaGraphicsUnmapResources(1, &cuda_res_[i], 0);
    }
}

float ChaosField::read_centre_amplitude() {
    cudaError_t e = cudaGraphicsMapResources(1, &cuda_res_[current_], 0);
    if (e != cudaSuccess) return -1.0f;
    cudaArray_t arr;
    e = cudaGraphicsSubResourceGetMappedArray(&arr, cuda_res_[current_], 0, 0);
    if (e != cudaSuccess) {
        cudaGraphicsUnmapResources(1, &cuda_res_[current_], 0);
        return -1.0f;
    }
    float v = -1.0f;
    cudaMemcpy3DParms cp = {};
    cp.srcArray = arr;
    cp.srcPos = { (size_t)resolution_ / 2, (size_t)resolution_ / 2, (size_t)resolution_ / 2 };
    cp.dstPtr = make_cudaPitchedPtr(&v, sizeof(float), 1, 1);
    cp.extent = { 1, 1, 1 };
    cp.kind = cudaMemcpyDeviceToHost;
    cudaMemcpy3D(&cp);
    cudaGraphicsUnmapResources(1, &cuda_res_[current_], 0);
    return v;
}

void ChaosField::draw(const float* view, const float* proj,
                      const float* camera_pos_xyz) const {
    glDisable(GL_DEPTH_TEST);
    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

    raymarch_prog_.use();
    raymarch_prog_.set_mat4("u_view", view);
    raymarch_prog_.set_mat4("u_proj", proj);
    raymarch_prog_.set_vec3("u_cam_pos", camera_pos_xyz[0], camera_pos_xyz[1], camera_pos_xyz[2]);
    raymarch_prog_.set_float("u_half_extent", world_half_extent_);
    raymarch_prog_.set_int("u_volume", 0);
    glActiveTexture(GL_TEXTURE0);
    glBindTexture(GL_TEXTURE_3D, gl_tex_[current_]);

    glBindVertexArray(vao_);
    glDrawArrays(GL_TRIANGLES, 0, 3);
    glBindVertexArray(0);

    glDisable(GL_BLEND);
    glEnable(GL_DEPTH_TEST);
}

void ChaosField::shutdown() {
    for (int i = 0; i < 2; i++) {
        if (cuda_res_[i]) { cudaGraphicsUnregisterResource(cuda_res_[i]); cuda_res_[i] = nullptr; }
        if (gl_tex_[i])   { glDeleteTextures(1, &gl_tex_[i]); gl_tex_[i] = 0; }
    }
    if (vao_) { glDeleteVertexArrays(1, &vao_); vao_ = 0; }
}

} // namespace astra_viz
