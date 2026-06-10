#version 460 core

in float v_axis_t;
out vec4 frag;

void main() {
    // Translucent cyan-blue per spec §6 step 10. Brighter at the apex, fading
    // along the cone length so the boundary doesn't read as a hard sheet.
    vec3  col = vec3(0.45, 0.85, 1.00);
    float a   = mix(0.45, 0.10, v_axis_t);   // apex 0.45 alpha; base 0.10
    frag = vec4(col, a);
}
