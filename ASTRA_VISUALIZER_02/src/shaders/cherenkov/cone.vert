#version 460 core

// Cone vertex shader. The mesh is a unit cone (apex at origin, axis +z, base
// radius 1 at z=1). The vertex shader scales it into world space:
//   - base radius = tan(half_angle) * length
//   - apex translated to u_apex
//   - axis rotated from +z to u_axis (orthonormal basis built per-frame)

layout(location = 0) in vec3 a_pos;

uniform mat4  u_view;
uniform mat4  u_proj;
uniform vec3  u_axis;
uniform vec3  u_apex;
uniform float u_length;
uniform float u_half_angle;

out float v_axis_t;        // 0 at apex, 1 at base; used by frag for falloff

void main() {
    float base_radius = tan(u_half_angle) * u_length;
    // Scale the model: x, y -> base_radius * (x, y); z -> length * z
    vec3 m = vec3(a_pos.x * base_radius, a_pos.y * base_radius, a_pos.z * u_length);

    // Build an orthonormal basis where +z aligns with u_axis.
    vec3 axis = normalize(u_axis);
    vec3 helper = (abs(axis.y) > 0.9) ? vec3(1.0, 0.0, 0.0) : vec3(0.0, 1.0, 0.0);
    vec3 right = normalize(cross(helper, axis));
    vec3 up    = cross(axis, right);

    vec3 world = u_apex + right * m.x + up * m.y + axis * m.z;
    gl_Position = u_proj * u_view * vec4(world, 1.0);
    v_axis_t = a_pos.z;
}
