// kernels/sanity.cu — CUDA sanity + CUDA-GL interop tests.
//
// run_sanity_check(): proves nvcc + CUDA runtime + linkage are functional.
// run_cuda_gl_interop_check(): proves cudaGraphicsGLRegisterImage round-trip
// (the pattern used by V2+ volume renderer per DESIGN_SPEC §2.4).
//
// Both functions are deliberately small and self-contained so they're easy
// to diagnose when something on a new machine breaks.

#include "kernels.h"

#include <glad/gl.h>
#include <cuda_runtime.h>
#include <cuda_gl_interop.h>
#include <surface_indirect_functions.h>

#include <cstdio>
#include <cstdint>

namespace astra::kernels {

namespace {

__global__ void k_fill_squares(int* dst, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) dst[i] = i * i;
}

__global__ void k_write_surface_2d(cudaSurfaceObject_t surf, int w, int h) {
    int x = blockIdx.x * blockDim.x + threadIdx.x;
    int y = blockIdx.y * blockDim.y + threadIdx.y;
    if (x >= w || y >= h) return;
    // Pack (R, G, B, A) = (x, y, x+y, 255) into RGBA8.
    uchar4 px;
    px.x = static_cast<unsigned char>(x);
    px.y = static_cast<unsigned char>(y);
    px.z = static_cast<unsigned char>(x + y);
    px.w = 255;
    // x byte offset within the row.
    surf2Dwrite(px, surf, x * static_cast<int>(sizeof(uchar4)), y);
}

bool log_cuda_err(cudaError_t e, const char* where) {
    if (e == cudaSuccess) return true;
    std::fprintf(stderr, "[CUDA] %s failed: %s\n", where, cudaGetErrorString(e));
    return false;
}

}  // namespace

bool run_sanity_check() {
    constexpr int N = 1024;
    int* d_buf = nullptr;
    if (!log_cuda_err(cudaMalloc(reinterpret_cast<void**>(&d_buf), N * sizeof(int)),
                      "cudaMalloc(d_buf)")) {
        return false;
    }

    int blocks = (N + 255) / 256;
    k_fill_squares<<<blocks, 256>>>(d_buf, N);

    cudaError_t launch_err = cudaGetLastError();
    if (!log_cuda_err(launch_err, "k_fill_squares launch")) {
        cudaFree(d_buf);
        return false;
    }

    if (!log_cuda_err(cudaDeviceSynchronize(), "cudaDeviceSynchronize")) {
        cudaFree(d_buf);
        return false;
    }

    int h_buf[N];
    if (!log_cuda_err(cudaMemcpy(h_buf, d_buf, N * sizeof(int), cudaMemcpyDeviceToHost),
                      "cudaMemcpy(d->h)")) {
        cudaFree(d_buf);
        return false;
    }
    cudaFree(d_buf);

    long long sum = 0;
    long long expected = 0;
    for (int i = 0; i < N; i++) {
        sum      += h_buf[i];
        expected += static_cast<long long>(i) * i;
    }
    if (sum != expected) {
        std::fprintf(stderr, "[CUDA] sanity checksum mismatch: got %lld, expected %lld\n",
                     sum, expected);
        return false;
    }
    return true;
}

bool run_cuda_gl_interop_check() {
    constexpr int W = 16;
    constexpr int H = 16;

    // Create + initialize a GL 2D texture.
    GLuint tex = 0;
    glGenTextures(1, &tex);
    glBindTexture(GL_TEXTURE_2D, tex);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, W, H, 0,
                 GL_RGBA, GL_UNSIGNED_BYTE, nullptr);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glBindTexture(GL_TEXTURE_2D, 0);

    GLenum gl_err = glGetError();
    if (gl_err != GL_NO_ERROR) {
        std::fprintf(stderr, "[GL] glTexImage2D failed: 0x%x\n", gl_err);
        glDeleteTextures(1, &tex);
        return false;
    }

    // Register for CUDA surface write.
    cudaGraphicsResource* cu_res = nullptr;
    if (!log_cuda_err(cudaGraphicsGLRegisterImage(
                          &cu_res, tex, GL_TEXTURE_2D,
                          cudaGraphicsRegisterFlagsSurfaceLoadStore),
                      "cudaGraphicsGLRegisterImage")) {
        glDeleteTextures(1, &tex);
        return false;
    }

    if (!log_cuda_err(cudaGraphicsMapResources(1, &cu_res), "cudaGraphicsMapResources")) {
        cudaGraphicsUnregisterResource(cu_res);
        glDeleteTextures(1, &tex);
        return false;
    }

    cudaArray_t array = nullptr;
    if (!log_cuda_err(cudaGraphicsSubResourceGetMappedArray(&array, cu_res, 0, 0),
                      "cudaGraphicsSubResourceGetMappedArray")) {
        cudaGraphicsUnmapResources(1, &cu_res);
        cudaGraphicsUnregisterResource(cu_res);
        glDeleteTextures(1, &tex);
        return false;
    }

    cudaResourceDesc rd{};
    rd.resType         = cudaResourceTypeArray;
    rd.res.array.array = array;
    cudaSurfaceObject_t surf = 0;
    if (!log_cuda_err(cudaCreateSurfaceObject(&surf, &rd), "cudaCreateSurfaceObject")) {
        cudaGraphicsUnmapResources(1, &cu_res);
        cudaGraphicsUnregisterResource(cu_res);
        glDeleteTextures(1, &tex);
        return false;
    }

    dim3 block(8, 8, 1);
    dim3 grid((W + 7) / 8, (H + 7) / 8, 1);
    k_write_surface_2d<<<grid, block>>>(surf, W, H);
    cudaError_t launch_err = cudaGetLastError();
    if (!log_cuda_err(launch_err, "k_write_surface_2d launch")) {
        cudaDestroySurfaceObject(surf);
        cudaGraphicsUnmapResources(1, &cu_res);
        cudaGraphicsUnregisterResource(cu_res);
        glDeleteTextures(1, &tex);
        return false;
    }
    log_cuda_err(cudaDeviceSynchronize(), "cudaDeviceSynchronize after surface write");

    cudaDestroySurfaceObject(surf);
    cudaGraphicsUnmapResources(1, &cu_res);
    cudaGraphicsUnregisterResource(cu_res);

    // Read back via GL.
    unsigned char host_px[W * H * 4];
    glBindTexture(GL_TEXTURE_2D, tex);
    glGetTexImage(GL_TEXTURE_2D, 0, GL_RGBA, GL_UNSIGNED_BYTE, host_px);
    GLenum readback_err = glGetError();
    glBindTexture(GL_TEXTURE_2D, 0);
    glDeleteTextures(1, &tex);
    if (readback_err != GL_NO_ERROR) {
        std::fprintf(stderr, "[GL] glGetTexImage failed: 0x%x\n", readback_err);
        return false;
    }

    // Verify checksum: every pixel should be (x, y, x+y, 255).
    int mismatches = 0;
    for (int y = 0; y < H; y++) {
        for (int x = 0; x < W; x++) {
            const unsigned char* p = host_px + (y * W + x) * 4;
            unsigned char want_r = static_cast<unsigned char>(x);
            unsigned char want_g = static_cast<unsigned char>(y);
            unsigned char want_b = static_cast<unsigned char>(x + y);
            unsigned char want_a = 255;
            if (p[0] != want_r || p[1] != want_g || p[2] != want_b || p[3] != want_a) {
                mismatches++;
            }
        }
    }
    if (mismatches > 0) {
        std::fprintf(stderr, "[INTEROP] %d/%d pixels mismatched\n", mismatches, W * H);
        return false;
    }
    return true;
}

}  // namespace astra::kernels
