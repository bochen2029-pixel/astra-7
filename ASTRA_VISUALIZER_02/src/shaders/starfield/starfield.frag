#version 460 core

in vec3 v_color;
out vec4 frag;

void main() {
    // Disc-shaped point with soft falloff so 1-2 px stars don't look square.
    vec2 d = gl_PointCoord - vec2(0.5);
    float r2 = dot(d, d);
    if (r2 > 0.25) discard;
    float fall = smoothstep(0.25, 0.05, r2);
    frag = vec4(v_color * fall, 1.0);
}
