import os
import subprocess
import time
import random
import glob
import re
import pathlib
import logging as log
import argparse

def get_benchmark_dirs():
  dirs = ['Benchmarks/Algorithm_Benchmarks', 'Benchmarks/Performance_Benchmarks']
  random.shuffle(dirs)
  return dirs

def compile_c_source(c_source, c_out, opt_level):
  try:
    subprocess.run(['gcc', '-w', f'-O{opt_level}', '-xc', '-', '-o', c_out, '-I/usr/include/apr-1.0', '-lapr-1', '-lpthread', '-lgmp'], input=c_source, check=True, text=True)
    return True
  except subprocess.CalledProcessError:
    log.error("C compilation failed")
    return False

def compile_rust(rust_file, rust_dir, rust_out, opt_level):
  flags = f"-A warnings -C opt-level={opt_level}"
  os.environ["RUSTFLAGS"] = flags
  try:
    if os.path.exists(rust_file):
      subprocess.run(['rustc', *flags.split(), rust_file, '-o', rust_out], check=True)
    else:
      subprocess.run(['cargo', 'build', '--release'], check=True,
                     cwd=rust_dir)
    return True
  except subprocess.CalledProcessError:
    log.error("Rust compilation failed")
    return False

def run_c_benchmark(c_out, input_data_file):
  try:
    start_time = time.time()
    c_output = subprocess.run([c_out], stdin=open(input_data_file), capture_output=True, text=True, check=True)
    # c_time = float(re.search(r'(\d+\.?\d+)', c_output.stdout).group(1))
    elapsed_time = time.time() - start_time
    log.info(f"C output: {c_output.stdout}")
    return elapsed_time
  except:
    log.error("C benchmark failed")
    return None

def run_rust_benchmark(rust_file, rust_out, rust_dir, input_data_file):
  try:
    start_time = time.time()
    if os.path.exists(rust_file):
      rust_output = subprocess.run([rust_out], stdin=open(input_data_file), capture_output=True, text=True, check=True)
    else:
      rust_output = subprocess.run(['cargo', 'run', '--release'],
                     cwd=rust_dir,
                     stdin=open(input_data_file),
                     capture_output=True,
                     text=True,
                     check=True)
    elapsed_time = time.time() - start_time
    # Keep original time parsing logic as backup/verification
    # parsed_time = float(re.search(r'(\d+\.?\d+)', rust_output.stdout).group(1))
    log.info(f"Rust output: {rust_output.stdout}")
    return elapsed_time
  except:
    log.error("Rust benchmark failed")
    return None

def write_results(results_file, base_name, c_time, rust_time):
  log.info(f"\nResults for {base_name}:")
  log.info(f"C time: {c_time:.3f}s")
  log.info(f"Rust time: {rust_time:.3f}s")
  log.info(f"Rust is {c_time/rust_time:.2f}x faster than C")
  
  if not os.path.exists(results_file):
    with open(results_file, "w") as f:
      f.write("algorithm,c_time,rust_time,speedup\n")
      
  with open(results_file, "a") as f:
    speedup = c_time/rust_time
    f.write(f"{base_name},{c_time:.3f},{rust_time:.3f},{speedup:.2f}\n")

def run_benchmark(d, c_file, input_data_file, opt_level, results_file):
  base_name = os.path.splitext(os.path.basename(c_file))[0]
  rust_file = f"{d}/Rust/{base_name}.rs"
  rust_dir = f"{d}/Rust/{base_name}"

  # Check if already evaluated in results.csv
  if os.path.exists(results_file):
    with open(results_file, "r") as f:
      if any(line.startswith(base_name + ",") for line in f):
        print(f"Skipping {base_name} as it was already evaluated")
        return

  log.info(f"Evaluating {base_name}")

  # print(f"Rust file: {rust_file}", os.path.exists(rust_file))
  # print(f"Rust dir: {rust_dir}", os.path.exists(rust_dir))
  
  if not (os.path.exists(rust_file) or os.path.exists(rust_dir)):
    log.info(f"Skipping {base_name} because it doesn't exist for rust")
    return

  input_data = pathlib.Path(input_data_file).read_text()
  input_data_list = input_data.strip().split()
  log.info(f"Input data length: {len(input_data_list)}")
    
  c_out = f"{d}/C/{base_name}.elf"
  c_source = pathlib.Path(c_file).read_text()
  c_source = c_source.replace("int n = 97;", f"int n = {len(input_data_list)};")
  if not compile_c_source(c_source, c_out, opt_level):
    return

  rust_out = f"{d}/Rust/{base_name}.elf"
  if not compile_rust(rust_file, rust_dir, rust_out, opt_level):
    return
    
  c_time = run_c_benchmark(c_out, input_data_file)
  if c_time is None:
    return
    
  rust_time = run_rust_benchmark(rust_file, rust_out, rust_dir, input_data_file)
  if rust_time is None:
    return
    
  write_results(results_file, base_name, c_time, rust_time)

def main():
  parser = argparse.ArgumentParser(description='Run C vs Rust benchmarks')
  parser.add_argument('--benchmark', type=str, help='Specific benchmark to run (without extension)')
  parser.add_argument('--opt-level', type=int, default=2, help='Optimization level (default: 2)')
  parser.add_argument('--input-data', type=str, default='Benchmarks/Algorithm_Benchmarks/input', help='Input data file path')
  parser.add_argument('-o', '--output', type=str, default='results.csv', help='Output file path')
  args = parser.parse_args()

  benchmark_dirs = get_benchmark_dirs()
  input_data_file = pathlib.Path(args.input_data).absolute()

  log.basicConfig(
      level=log.INFO,
      format='\033[36m%(asctime)s\033[0m - \033[1;33m%(levelname)s\033[0m - \033[32m%(message)s\033[0m',
      datefmt='%Y-%m-%d %H:%M:%S'
  )

  total_benchmarks = 0
  if args.benchmark:
    # Run specific benchmark
    for d in benchmark_dirs:
      c_file = f"{d}/C/{args.benchmark}.c"
      if os.path.exists(c_file):
        run_benchmark(d, c_file, input_data_file, args.opt_level, args.output)
        total_benchmarks += 1
        break
    else:
      log.error(f"Benchmark {args.benchmark} not found")
  else:
    # Run all benchmarks
    for d in benchmark_dirs:
      c_files = glob.glob(f"{d}/C/*.c")
      random.shuffle(c_files)
      
      for c_file in c_files:
        run_benchmark(d, c_file, input_data_file, args.opt_level, args.output)
        total_benchmarks += 1
  log.info(f"Total benchmarks: {total_benchmarks}")

if __name__ == "__main__":
  main()