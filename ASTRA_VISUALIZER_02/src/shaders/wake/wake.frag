#version 460 core

in  float v_age01;
out vec4  frag;

void main() {
    // Old end faints; new end bright. Cyan-blue tint matches the warp bubble palette.
    float alpha = mix(0.0, 0.9, v_age01);
    vec3  col   = mix(vec3(0.15, 0.25, 0.55), vec3(0.55, 0.85, 1.00), v_age01);
    frag = vec4(col, alpha);
}
