#version 460 core

layout(location = 0) in vec3 a_pos;
layout(location = 1) in vec3 a_nrm;

uniform mat4 u_view;
uniform mat4 u_proj;

out vec3 v_world_pos;
out vec3 v_world_nrm;

void main() {
    v_world_pos = a_pos;
    v_world_nrm = normalize(a_nrm);
    gl_Position = u_proj * u_view * vec4(a_pos, 1.0);
}
