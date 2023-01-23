#version 450

layout(location = 0) in vec2 uv;

layout(binding = 1) uniform sampler2D texSampler;

layout(location = 0) out vec4 outColor;
layout(location = 1) out vec4 extra;

void main(){
	outColor = texture(texSampler, uv) * vec4(0.5,0.5,0,1);
	extra = vec4(1);
}