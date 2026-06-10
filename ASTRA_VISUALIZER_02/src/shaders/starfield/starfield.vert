#version 460 core

layout(location = 0) in vec3  a_pos;
layout(location = 1) in vec3  a_color;
layout(location = 2) in float a_size;

uniform mat4  u_view;
uniform mat4  u_proj;
uniform vec3  u_ship_vel_dir;     // unit; +z by default
uniform float u_beta;             // [-0.9999, 0.9999]; 0 = no aberration / no Doppler

out vec3 v_color;

// Relativistic aberration for a star direction nhat seen by an observer moving
// at beta along v_dir. Per spec §3.4: tan(theta'/2) = tan(theta/2) * sqrt((1-b)/(1+b))
// for stars in front; equivalent in 3D by rotating the angle around the axis
// (v_dir x nhat). Implemented as a closed-form mapping of nhat -> n'.
vec3 sr_aberration(vec3 nhat, vec3 v_dir, float beta) {
    if (abs(beta) < 1.0e-4) return nhat;
    float cos_theta = dot(normalize(nhat), v_dir);
    cos_theta = clamp(cos_theta, -1.0, 1.0);
    float cos_theta_new = (cos_theta - beta) / (1.0 - beta * cos_theta);
    cos_theta_new = clamp(cos_theta_new, -1.0, 1.0);
    // Reconstruct n' in the same plane spanned by (nhat, v_dir).
    float sin_theta_new = sqrt(max(0.0, 1.0 - cos_theta_new * cos_theta_new));
    vec3  axial = v_dir * cos_theta_new;
    vec3  perp_axis = nhat - v_dir * cos_theta;
    float perp_len  = length(perp_axis);
    vec3  perp = (perp_len > 1.0e-6) ? perp_axis / perp_len : vec3(0.0);
    return normalize(axial + perp * sin_theta_new);
}

void main() {
    mat4 view_no_trans = u_view;
    view_no_trans[3].xyz = vec3(0.0);

    vec3 nhat = normalize(a_pos);
    vec3 n_aberrated = sr_aberration(nhat, u_ship_vel_dir, u_beta);

    // Per-star Doppler tint along the star direction. Stars in the forward
    // hemisphere blueshift (warmer / brighter); rear-hemisphere redshift
    // (dimmer / redder). Uses the SR longitudinal Doppler at each star's
    // line-of-sight beta component.
    float cos_los = dot(nhat, u_ship_vel_dir);
    float beta_los = u_beta * cos_los;   // approaching when nhat dot v > 0 if u_beta < 0 etc.
    float bc = clamp(beta_los, -0.9999, 0.9999);
    float doppler = sqrt((1.0 + bc) / (1.0 - bc));  // > 1 = brighter / blueshift

    vec3 color = a_color * doppler;
    // Crude wavelength shift: scale red down on blueshift, scale red up on redshift.
    color.r *= mix(1.0, 0.7, max(0.0, bc));
    color.g *= 1.0;
    color.b *= mix(1.0, 0.5, max(0.0, -bc));

    vec4 clip = u_proj * view_no_trans * vec4(n_aberrated * length(a_pos), 1.0);
    gl_Position = clip;
    gl_PointSize = a_size;
    v_color = color;
}
