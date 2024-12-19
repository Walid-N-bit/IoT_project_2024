import os

# Input and output file paths
tflite_file = "trained.tflite"
output_header = "model.h"

# Read the .tflite file
with open(tflite_file, "rb") as f:
    tflite_data = f.read()

# Write to header file with proper formatting
with open(output_header, "w") as f:
    f.write("/* This file contains the TensorFlow Lite model in C header format. */\n")
    f.write("#ifndef MODEL_H\n#define MODEL_H\n\n")
    f.write("#include <stddef.h>\n#include <stdint.h>\n\n")
    f.write("alignas(16) const unsigned char model_data[] = {\n")

    # Convert bytes to hex and write in rows of 12
    for i in range(0, len(tflite_data), 12):
        row = tflite_data[i:i+12]
        hex_values = ", ".join(f"0x{b:02X}" for b in row)
        f.write(f"    {hex_values},\n")

    f.write("};\n\n")
    f.write(f"const size_t model_data_len = {len(tflite_data)};\n")
    f.write("#endif // MODEL_H\n")
