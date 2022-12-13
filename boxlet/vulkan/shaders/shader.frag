#version 450

layout(location = 0) in vec3 fragColor;
layout(location = 1) in vec2 uv;

layout(binding = 0) uniform sampler2D texSampler;

layout(location = 0) out vec4 outColor;

void main(){
	// outColor = vec4(fragColor, 1.0) / max(fragColor.x, max(fragColor.y, fragColor.z));
	outColor = texture(texSampler, uv) * (vec4(fragColor, 1) * 0.5 + 0.5);
}