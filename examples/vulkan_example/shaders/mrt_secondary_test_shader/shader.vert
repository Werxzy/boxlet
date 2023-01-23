#version 450

layout(location = 0) in vec3 position;
layout(location = 1) in vec2 texcoord;
layout(location = 2) in mat4 model;

layout(binding = 2) uniform UniformBufferObject {
    vec3 color1;
    vec3 color2;
    vec3 color3;
} ubo;

layout (push_constant) uniform constants {
	mat4 viewProj;
} box;

layout(location = 0) out vec2 uv;

void main(){
	gl_Position = box.viewProj * model * vec4(position + ubo.color1, 1.0);
	uv = texcoord;
}