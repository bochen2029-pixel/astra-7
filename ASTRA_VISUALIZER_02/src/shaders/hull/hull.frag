#version 460 core

in vec3 v_world_pos;
in vec3 v_world_nrm;

uniform float u_time;

out vec4 frag;

void main() {
    // simple two-light Phong: warm key light from +x +y, cool fill from -x
    vec3 N = normalize(v_world_nrm);
    vec3 L1 = normalize(vec3( 0.6,  0.5,  0.3));
    vec3 L2 = normalize(vec3(-0.6,  0.2, -0.3));
    float d1 = max(dot(N, L1), 0.0);
    float d2 = max(dot(N, L2), 0.0);

    vec3 base = vec3(0.55, 0.58, 0.62);     // brushed-metal grey
    vec3 warm = vec3(1.00, 0.85, 0.65);
    vec3 cool = vec3(0.40, 0.55, 0.85);

    vec3 color = base * (0.10 + 0.75 * d1) * warm + base * 0.20 * d2 * cool;

    // subtle panel-line shading along long axis so the hull doesn't look like
    // a single shaded blob. Sin-pulse along x.
    float panels = 0.5 + 0.5 * sin(v_world_pos.x * 0.30);
    color *= 0.92 + 0.08 * panels;

    frag = vec4(color, 1.0);
}
