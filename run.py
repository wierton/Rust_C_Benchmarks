import os
import subprocess
import time
import random
import glob
import re
import pathlib

def get_benchmark_dirs():
  dirs = ['Benchmarks/Algorithm_Benchmarks', 'Benchmarks/Performance_Benchmarks']
  random.shuffle(dirs)
  return dirs

def get_input_data():
  input_path = str(pathlib.Path('Benchmarks/Algorithm_Benchmarks/input').absolute())
  assert os.path.exists(input_path)
  return input_path

def compile_c(c_file, c_out):
  try:
    subprocess.run(['gcc', '-O2', c_file, '-o', c_out], check=True)
    return True
  except subprocess.CalledProcessError:
    print("C compilation failed")
    return False

def compile_rust(rust_file, rust_dir, rust_out):
  os.environ["RUSTFLAGS"] = "-A warnings"
  try:
    if os.path.exists(rust_file):
      subprocess.run(['rustc', '-A', 'warnings', '-O', rust_file, '-o', rust_out], check=True)
    else:
      os.chdir(rust_dir)
      subprocess.run(['cargo', 'build', '--release'], check=True)
      os.chdir('../../..')
    return True
  except subprocess.CalledProcessError:
    print("Rust compilation failed")
    return False

def run_c_benchmark(c_out, input_data):
  try:
    c_output = subprocess.run([c_out], stdin=open(input_data), capture_output=True, text=True, check=True)
    c_time = float(re.search(r'(\d+\.?\d+)', c_output.stdout).group(1))
    print(f"C output: {c_output.stdout}")
    return c_time
  except:
    print("C benchmark failed")
    return None

def run_rust_benchmark(rust_file, rust_out, rust_dir, input_data):
  try:
    if os.path.exists(rust_file):
      rust_output = subprocess.run([rust_out], stdin=open(input_data), capture_output=True, text=True, check=True)
    else:
      rust_output = subprocess.run(['cargo', 'run', '--release'],
                     cwd=rust_dir,
                     stdin=open(input_data),
                     capture_output=True,
                     text=True,
                     check=True)
    rust_time = float(re.search(r'(\d+\.?\d+)', rust_output.stdout).group(1))
    print(f"Rust output: {rust_output.stdout}")
    return rust_time
  except:
    print("Rust benchmark failed")
    return None

def write_results(base_name, c_time, rust_time):
  print(f"\nResults for {base_name}:")
  print(f"C time: {c_time:.3f}s")
  print(f"Rust time: {rust_time:.3f}s")
  print(f"Rust is {c_time/rust_time:.2f}x faster than C")
  
  if not os.path.exists("results.csv"):
    with open("results.csv", "w") as f:
      f.write("algorithm,c_time,rust_time,speedup\n")
      
  with open("results.csv", "a") as f:
    speedup = c_time/rust_time
    f.write(f"{base_name},{c_time:.3f},{rust_time:.3f},{speedup:.2f}\n")

def main():
  benchmark_dirs = get_benchmark_dirs()
  input_data = get_input_data()

  for d in benchmark_dirs:
    c_files = glob.glob(f"{d}/C/*.c")
    random.shuffle(c_files)
    
    for c_file in c_files:
      base_name = os.path.splitext(os.path.basename(c_file))[0]
      rust_file = f"{d}/Rust/{base_name}.rs"
      rust_dir = f"{d}/Rust/{base_name}"

      print(f"Evaluating {base_name}")
      
      if not (os.path.exists(rust_file) or os.path.exists(rust_dir)):
        print(f"Skipping {base_name} because it doesn't exist for rust")
        continue
        
      c_out = f"{d}/C/{base_name}.elf"
      if not compile_c(c_file, c_out):
        continue

      rust_out = f"{d}/Rust/{base_name}.elf"
      if not compile_rust(rust_file, rust_dir, rust_out):
        continue
        
      c_time = run_c_benchmark(c_out, input_data)
      if c_time is None:
        continue
        
      rust_time = run_rust_benchmark(rust_file, rust_out, rust_dir, input_data)
      if rust_time is None:
        continue
        
      write_results(base_name, c_time, rust_time)

if __name__ == "__main__":
  main()