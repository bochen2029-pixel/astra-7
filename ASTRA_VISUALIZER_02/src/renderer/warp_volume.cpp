#include "renderer/warp_volume.h"
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

bool WarpVolume::init(int resolution, float world_half_extent) {
    resolution_ = resolution;
    world_half_extent_ = world_half_extent;

    glGenTextures(1, &gl_tex_);
    glBindTexture(GL_TEXTURE_3D, gl_tex_);
    glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE);
    std::vector<float> zeros((size_t)resolution_ * resolution_ * resolution_, 0.0f);
    glTexImage3D(GL_TEXTURE_3D, 0, GL_R32F, resolution_, resolution_, resolution_,
                 0, GL_RED, GL_FLOAT, zeros.data());
    glBindTexture(GL_TEXTURE_3D, 0);

    if (!ok(cudaGraphicsGLRegisterImage(&cuda_res_, gl_tex_, GL_TEXTURE_3D,
                                         cudaGraphicsRegisterFlagsSurfaceLoadStore),
            "cudaGraphicsGLRegisterImage")) {
        return false;
    }

    glGenVertexArrays(1, &vao_);

    const std::string& root = astra_viz::exe_directory();
    if (!raymarch_prog_.load_from_files(root + "shaders/warp_volume/raymarch.vert",
                                         root + "shaders/warp_volume/raymarch.frag")) {
        astra_viz::log::error("warp_volume raymarch program load failed");
        return false;
    }

    astra_viz::log::info("WarpVolume: %d^3 GL_R32F texture (half-extent %.1f m) ready",
                         resolution_, world_half_extent_);
    return true;
}

void WarpVolume::update(const WarpFieldParams& params) {
    if (!cuda_res_) return;

    cudaError_t e = cudaGraphicsMapResources(1, &cuda_res_, 0);
    if (e != cudaSuccess) {
        astra_viz::log::error("cudaGraphicsMapResources: %s", cudaGetErrorString(e));
        return;
    }
    cudaArray_t arr = nullptr;
    e = cudaGraphicsSubResourceGetMappedArray(&arr, cuda_res_, 0, 0);
    if (e != cudaSuccess) {
        astra_viz::log::error("cudaGraphicsSubResourceGetMappedArray: %s", cudaGetErrorString(e));
        cudaGraphicsUnmapResources(1, &cuda_res_, 0);
        return;
    }

    cudaResourceDesc rd = {};
    rd.resType = cudaResourceTypeArray;
    rd.res.array.array = arr;
    cudaSurfaceObject_t surf = 0;
    e = cudaCreateSurfaceObject(&surf, &rd);
    if (e != cudaSuccess) {
        astra_viz::log::error("cudaCreateSurfaceObject: %s", cudaGetErrorString(e));
        cudaGraphicsUnmapResources(1, &cuda_res_, 0);
        return;
    }

    WarpFieldParams p = params;
    p.world_half_extent = world_half_extent_;
    e = launch_warp_field_kernel(surf, resolution_, p);
    if (e != cudaSuccess) {
        astra_viz::log::error("warp_field kernel: %s", cudaGetErrorString(e));
    }

    cudaDestroySurfaceObject(surf);
    cudaGraphicsUnmapResources(1, &cuda_res_, 0);
}

void WarpVolume::draw(const float* view, const float* proj,
                      const float* camera_pos_xyz) const {
    if (!cuda_res_) return;

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
    glBindTexture(GL_TEXTURE_3D, gl_tex_);

    glBindVertexArray(vao_);
    glDrawArrays(GL_TRIANGLES, 0, 3);
    glBindVertexArray(0);

    glDisable(GL_BLEND);
    glEnable(GL_DEPTH_TEST);
}

void WarpVolume::shutdown() {
    if (cuda_res_) { cudaGraphicsUnregisterResource(cuda_res_); cuda_res_ = nullptr; }
    if (vao_)    { glDeleteVertexArrays(1, &vao_);  vao_ = 0; }
    if (gl_tex_) { glDeleteTextures(1, &gl_tex_);   gl_tex_ = 0; }
}

} // namespace astra_viz
