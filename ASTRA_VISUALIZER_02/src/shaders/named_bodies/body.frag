#version 460 core

in vec2 v_local;
uniform vec3 u_tint;
out vec4 frag;

void main() {
    float r2 = dot(v_local, v_local);
    if (r2 > 1.0) discard;

    // Hard inner disc (r2 < 0.45) shows pure u_tint; alpha=1. Soft outer halo
    // fades alpha to 0 by r2=1.0. The pure-tint inner disc lets pixel
    // assertions sample expected channel values exactly: at the body centre
    // pixel the framebuffer reads u_tint directly without shader-side scaling.
    float alpha = (r2 < 0.45) ? 1.0 : smoothstep(1.0, 0.45, r2);
    frag = vec4(u_tint, alpha);
}
