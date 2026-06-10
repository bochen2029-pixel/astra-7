#version 460 core

// V5 warp-bubble ray-march. The 3D texture holds W(x) computed by warp_field.cu.
// Cube of edge 2*u_half_extent centred at world origin contains the bubble.
// Aesthetic: violet-blue interior with a brighter ring at high |grad W|.

in vec2 v_uv;

uniform mat4  u_view;
uniform mat4  u_proj;
uniform vec3  u_cam_pos;
uniform float u_half_extent;
uniform sampler3D u_volume;

out vec4 frag;

vec3 ray_direction(vec2 uv) {
    vec4 clip = vec4(uv * 2.0 - 1.0, 1.0, 1.0);
    mat4 inv_proj = inverse(u_proj);
    mat4 inv_view = inverse(u_view);
    vec4 eye = inv_proj * clip;
    eye = vec4(eye.xy, -1.0, 0.0);
    return normalize((inv_view * eye).xyz);
}

bool intersect_cube(vec3 ro, vec3 rd, float h, out float t0, out float t1) {
    vec3 inv = 1.0 / rd;
    vec3 b0  = (-vec3(h) - ro) * inv;
    vec3 b1  = ( vec3(h) - ro) * inv;
    vec3 tmin = min(b0, b1);
    vec3 tmax = max(b0, b1);
    t0 = max(max(tmin.x, tmin.y), tmin.z);
    t1 = min(min(tmax.x, tmax.y), tmax.z);
    return t1 >= max(t0, 0.0);
}

// Cheap central-difference gradient magnitude of W. Used to highlight the
// bubble boundary where the metric changes fastest (per spec §6 ray-march
// gradient discipline). Texel-stride of 1 / 128 for a 128^3 volume; we use
// textureSize so it scales if resolution changes.
float grad_magnitude(vec3 uvw) {
    vec3 inv = 1.0 / vec3(textureSize(u_volume, 0));
    float dx = texture(u_volume, uvw + vec3(inv.x, 0, 0)).r
             - texture(u_volume, uvw - vec3(inv.x, 0, 0)).r;
    float dy = texture(u_volume, uvw + vec3(0, inv.y, 0)).r
             - texture(u_volume, uvw - vec3(0, inv.y, 0)).r;
    float dz = texture(u_volume, uvw + vec3(0, 0, inv.z)).r
             - texture(u_volume, uvw - vec3(0, 0, inv.z)).r;
    return length(vec3(dx, dy, dz));
}

void main() {
    float h = u_half_extent;
    vec3 ro = u_cam_pos;
    vec3 rd = ray_direction(v_uv);

    float t0, t1;
    if (!intersect_cube(ro, rd, h, t0, t1)) discard;
    t0 = max(t0, 0.0);

    const int STEPS = 96;
    float step_len = (t1 - t0) / float(STEPS);
    vec3  pos      = ro + rd * t0;
    vec3  step_vec = rd * step_len;

    // Bubble interior: violet-blue base; boundary: brighter cyan ring driven
    // by |grad W|. Spec §6 step 8: sharp |grad W| at the bubble wall.
    vec3 interior = vec3(0.22, 0.12, 0.55);
    vec3 boundary = vec3(0.65, 0.85, 1.00);

    vec4 accum = vec4(0.0);
    // V8 lensing-lite: add a tiny per-channel offset along the ray so the
    // boundary samples R/G/B at slightly different points. Approximates a
    // gradient-driven refraction without a real FBO-based post-pass. Full
    // FBO lensing planned for V9 alongside validation infrastructure.
    const float CHROMATIC_OFFSET = 0.06;
    for (int i = 0; i < STEPS; i++) {
        vec3 uvw = (pos / h) * 0.5 + 0.5;
        if (any(lessThan(uvw, vec3(0.0))) || any(greaterThan(uvw, vec3(1.0)))) {
            pos += step_vec;
            continue;
        }
        float W_r = texture(u_volume, uvw + step_vec * CHROMATIC_OFFSET / h).r;
        float W_g = texture(u_volume, uvw).r;
        float W_b = texture(u_volume, uvw - step_vec * CHROMATIC_OFFSET / h).r;
        float W   = W_g;
        if (W > 0.005) {
            float g = grad_magnitude(uvw);
            float boundary_mix = clamp(g * 5.0, 0.0, 1.0);
            vec3  col_base = mix(interior, boundary, boundary_mix);
            // Tint each channel by its own W sample so high |grad W| reveals chromatic offset.
            vec3  col = vec3(col_base.r * (0.85 + 0.30 * W_r),
                              col_base.g * (0.85 + 0.30 * W_g),
                              col_base.b * (0.85 + 0.30 * W_b));
            float opac = W * 0.04 + boundary_mix * W * 0.10;
            accum.rgb += (1.0 - accum.a) * col * opac;
            accum.a   += (1.0 - accum.a) * opac;
            if (accum.a > 0.97) break;
        }
        pos += step_vec;
    }
    if (accum.a < 0.001) discard;
    frag = accum;
}
