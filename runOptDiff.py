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

def compile_with_clang(c_file, out_file, opt_level):
    try:
        subprocess.run(['clang-18', f'-O{opt_level}', c_file, '-o', out_file, '-I/usr/include/apr-1.0', '-lapr-1', '-lpthread', '-lgmp'], check=True)
        return True
    except subprocess.CalledProcessError:
        log.error(f"Clang compilation failed with -O{opt_level}")
        return False

def compile_with_llvm_opt(c_file, out_file):
    try:
        ll_file = f"{os.path.splitext(out_file)[0]}.ll"
        opt_ll_file = f"{os.path.splitext(out_file)[0]}_opt.ll"
        
        # Generate LLVM IR
        subprocess.run(['clang-18', '-O3', '-S', '-emit-llvm', c_file, '-o', ll_file], check=True)
        
        # Optimize with opt
        subprocess.run(['opt-18', '-O3', ll_file, '-o', opt_ll_file], check=True)
        
        # Compile optimized IR to executable
        subprocess.run(['clang-18', '-O3', opt_ll_file, '-o', out_file, '-I/usr/include/apr-1.0', '-lapr-1', '-lpthread', '-lgmp'], check=True)
        
        return True
    except subprocess.CalledProcessError:
        log.error("LLVM optimization pipeline failed")
        return False

def run_benchmark_with_perf(executable, input_data_file):
    try:
        perf_output = subprocess.run(['perf', 'stat', '-e', 'cycles', executable], 
                                    stdin=open(input_data_file), 
                                    capture_output=True, 
                                    errors='ignore',
                                    text=True, 
                                    check=True)
        
        # Extract time and cycles from perf output
        time_match = re.search(r'(\d+\.\d+) seconds time elapsed', perf_output.stderr)
        cycles_match = re.search(r'(\d+,\d+|\d+)\s+cycles', perf_output.stderr)
        
        if time_match and cycles_match:
            elapsed_time = float(time_match.group(1))
            cycles = int(cycles_match.group(1).replace(',', ''))
            log.info(f"Time elapsed: {elapsed_time:.3f}s, Cycles: {cycles:,}")
            return elapsed_time, cycles
        else:
            log.error("Could not parse perf output")
            return None, None
    except subprocess.CalledProcessError:
        log.error("Benchmark execution failed")
        return None, None

def write_results(results_file, base_name, o2_time, o2_cycles, o3_time, o3_cycles, llvm_time, llvm_cycles):
    log.info(f"\nResults for {base_name}:")
    log.info(f"Clang -O2 time: {o2_time:.3f}s, cycles: {o2_cycles:,}")
    log.info(f"Clang -O3 time: {o3_time:.3f}s, cycles: {o3_cycles:,}")
    log.info(f"LLVM pipeline time: {llvm_time:.3f}s, cycles: {llvm_cycles:,}")
    
    if not os.path.exists(results_file):
        with open(results_file, "w") as f:
            f.write("algorithm,clang_o2_time,clang_o2_cycles,clang_o3_time,clang_o3_cycles,llvm_pipeline_time,llvm_pipeline_cycles\n")
            
    with open(results_file, "a") as f:
        f.write(f"{base_name},{o2_time:.3f},{o2_cycles},{o3_time:.3f},{o3_cycles},{llvm_time:.3f},{llvm_cycles}\n")

def run_benchmark(d, c_file, input_data_file, results_file):
    base_name = os.path.splitext(os.path.basename(c_file))[0]

    # Check if already evaluated in results.csv
    if os.path.exists(results_file):
        with open(results_file, "r") as f:
            if any(line.startswith(base_name + ",") for line in f):
                print(f"Skipping {base_name} as it was already evaluated")
                return

    log.info(f"Evaluating {base_name}")
    
    input_data = pathlib.Path(input_data_file).read_text()
    input_data_list = input_data.strip().split()
    log.info(f"Input data length: {len(input_data_list)}")
    
    # Prepare C source with correct input size
    c_source = pathlib.Path(c_file).read_text()
    c_source = c_source.replace("int n = 97;", f"int n = {len(input_data_list)};")
    
    # Write modified source to a temporary file
    temp_c_file = f"{d}/C/{base_name}_temp.c"
    with open(temp_c_file, "w") as f:
        f.write(c_source)
    
    # Compile with clang -O2
    o2_out = f"{d}/C/{base_name}_O2.elf"
    if not compile_with_clang(temp_c_file, o2_out, 2):
        os.remove(temp_c_file)
        return
    
    # Run with perf stat
    o2_time, o2_cycles = run_benchmark_with_perf(o2_out, input_data_file)
    if o2_time is None:
        os.remove(temp_c_file)
        return
    
    # Compile with clang -O3
    o3_out = f"{d}/C/{base_name}_O3.elf"
    if not compile_with_clang(temp_c_file, o3_out, 3):
        os.remove(temp_c_file)
        return
    
    # Run with perf stat
    o3_time, o3_cycles = run_benchmark_with_perf(o3_out, input_data_file)
    if o3_time is None:
        os.remove(temp_c_file)
        return
    
    # Compile with LLVM optimization pipeline
    llvm_out = f"{d}/C/{base_name}_LLVM.elf"
    if not compile_with_llvm_opt(temp_c_file, llvm_out):
        os.remove(temp_c_file)
        return
    
    # Run with perf stat
    llvm_time, llvm_cycles = run_benchmark_with_perf(llvm_out, input_data_file)
    if llvm_time is None:
        os.remove(temp_c_file)
        return
    
    # Clean up temporary file
    os.remove(temp_c_file)
    
    # Write results
    write_results(results_file, base_name, o2_time, o2_cycles, o3_time, o3_cycles, llvm_time, llvm_cycles)

def main():
    parser = argparse.ArgumentParser(description='Run C benchmarks with different optimization levels')
    parser.add_argument('--benchmark', type=str, help='Specific benchmark to run (without extension)')
    parser.add_argument('--input-data', type=str, default='Benchmarks/Algorithm_Benchmarks/input', help='Input data file path')
    parser.add_argument('-o', '--output', type=str, default='llvm-pipeline-results.csv', help='Output file path')
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
                run_benchmark(d, c_file, input_data_file, args.output)
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
              if os.path.exists(c_file):
                run_benchmark(d, c_file, input_data_file, args.output)
                total_benchmarks += 1
    
    log.info(f"Total benchmarks: {total_benchmarks}")

if __name__ == "__main__":
    main()