// kernels/kernels.h — C++ declarations for CUDA host functions.
//
// Each entry is a host function that internally launches a __global__ kernel.
// C++ TUs include this header; CUDA TUs implement these in matching .cu files.

#pragma once

namespace astra::kernels {

// Trivial sanity check: launches a kernel that writes i*i into N=1024 ints,
// copies back, verifies checksum. Returns true iff the kernel ran and the
// data matches. Proves the CUDA toolkit + nvcc + linkage are sane.
bool run_sanity_check();

// CUDA-GL interop sanity check: creates a small GL texture, registers it
// with CUDA, maps + writes to it from a CUDA surface, reads back via
// glGetTexImage. Returns true iff the round-trip preserves the written
// values. Proves the DESIGN_SPEC §2.4 dual-binding pattern is operational.
// Requires a current OpenGL 4.6 context; call only after gladLoadGL succeeds.
bool run_cuda_gl_interop_check();

}  // namespace astra::kernels
