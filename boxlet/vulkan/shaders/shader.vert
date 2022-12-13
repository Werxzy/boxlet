#version 450

layout(location = 0) in vec2 vertexPosition;
layout(location = 1) in vec3 vertexColor;
layout(location = 2) in mat4 model;

layout (push_constant) uniform constants {
	mat4 viewProj;
} box;

layout(location = 0) out vec3 fragColor;
layout(location = 1) out vec2 uv;

void main(){
	gl_Position = box.viewProj * model * vec4(vertexPosition, 0.0, 1.0);
	fragColor = vertexColor;
	uv = vertexPosition * 10;
}