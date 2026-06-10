#version 460 core

// Projects the body's world-space direction through the view+proj matrices to
// get a 2D centre, then expands a quad of u_radius_clip clip-space radius
// around it. The view's translation is stripped so the body sits at infinity.

uniform mat4  u_view;
uniform mat4  u_proj;
uniform vec3  u_dir;
uniform float u_radius_clip;

out vec2 v_local;       // [-1, 1] across the billboard for the disc fragment shader

void main() {
    mat4 view_no_trans = u_view;
    view_no_trans[3].xyz = vec3(0.0);
    vec4 clip = u_proj * view_no_trans * vec4(normalize(u_dir) * 1.0e6, 1.0);
    if (clip.w <= 0.0) {
        gl_Position = vec4(2.0, 2.0, 2.0, 1.0);  // off-screen
        v_local = vec2(0.0);
        return;
    }
    vec2 ndc = clip.xy / clip.w;

    // 6-vertex quad pattern via gl_VertexID. Two triangles.
    const vec2 corners[6] = vec2[6](
        vec2(-1,-1), vec2( 1,-1), vec2(-1, 1),
        vec2( 1,-1), vec2( 1, 1), vec2(-1, 1)
    );
    vec2 corner = corners[gl_VertexID];
    v_local = corner;
    gl_Position = vec4(ndc + corner * u_radius_clip, 0.0, 1.0);
}
