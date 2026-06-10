#version 460 core

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

// Heat colormap: deep purple low density -> red -> orange -> yellow high density.
// Different from warp_volume's violet-blue so the operator can tell chaos from warp at a glance.
vec3 heat_ramp(float v) {
    vec3 c0 = vec3(0.10, 0.02, 0.30);    // deep purple
    vec3 c1 = vec3(0.85, 0.18, 0.10);    // red
    vec3 c2 = vec3(1.00, 0.85, 0.10);    // yellow
    if (v < 0.5) return mix(c0, c1, v * 2.0);
    return mix(c1, c2, (v - 0.5) * 2.0);
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
    vec3 pos = ro + rd * t0;
    vec3 step_vec = rd * step_len;

    vec4 accum = vec4(0.0);
    for (int i = 0; i < STEPS; i++) {
        vec3 uvw = (pos / h) * 0.5 + 0.5;
        if (any(lessThan(uvw, vec3(0.0))) || any(greaterThan(uvw, vec3(1.0)))) {
            pos += step_vec;
            continue;
        }
        float v = texture(u_volume, uvw).r;
        if (v > 0.01) {
            vec3 col = heat_ramp(v);
            float opac = v * 0.06;
            accum.rgb += (1.0 - accum.a) * col * opac;
            accum.a   += (1.0 - accum.a) * opac;
            if (accum.a > 0.97) break;
        }
        pos += step_vec;
    }
    if (accum.a < 0.001) discard;
    frag = accum;
}
