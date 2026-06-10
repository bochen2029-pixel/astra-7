#version 460 core

layout(location = 0) in vec3 a_pos;

uniform mat4 u_view;
uniform mat4 u_proj;
uniform int  u_total;

out float v_age01;     // 0 = oldest, 1 = newest

void main() {
    v_age01 = (u_total > 1) ? (float(gl_VertexID) / float(u_total - 1)) : 1.0;
    gl_Position = u_proj * u_view * vec4(a_pos, 1.0);
}
