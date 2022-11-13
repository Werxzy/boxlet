# Semi-Depricated Code

The files here are mostly for reference from an older design.

## MultiModelRenderer

This renderer was designed to render different models each with different model matrices, but ran into issues with glMultiDrawElements not recognizing multiple divisors from `glVertexAttribDivisor` and mac not supporting `gl_DrawIDARB`.
