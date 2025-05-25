import socket
import json
import base64
import logging
import time
import concurrent.futures
import os
import csv

# Configuration
SERVER_ADDRESS = ('172.16.16.101',5000)
VOLUME_SIZES = ['10mb', '50mb', '100mb']
CLIENT_WORKERS = [1, 5, 50]
OPERATIONS = ['UPLOAD', 'GET']
RESULTS_FILE = 'multiprocess_serverworker_50.csv'

class StressTester:
    def __init__(self):
        self.results = []
        logging.basicConfig(level=logging.WARNING)

    def send_command(self, command_str=""):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(SERVER_ADDRESS)
        try:
            command_to_send = command_str + "\r\n\r\n"
            sock.sendall(command_to_send.encode())
            data_received = ""
            while True:
                data = sock.recv(65536)  # 64 Kb buffer
                if data:
                    data_received += data.decode()
                    if "\r\n\r\n" in data_received:
                        break
                else:
                    break
            return json.loads(data_received)
        except Exception as e:
            return {'status': 'ERROR', 'data': str(e)}
        finally:
            sock.close()

    def remote_upload(self, filename):
        start_time = time.time()
        try:
            with open(filename, 'rb') as f:
                content = base64.b64encode(f.read()).decode()
            file_size = os.path.getsize(filename)
            
            command_str = f"UPLOAD {filename} {content}"
            hasil = self.send_command(command_str)
            
            elapsed = time.time() - start_time
            throughput = file_size / elapsed if elapsed > 0 else 0
            
            if hasil['status'] == 'OK':
                return {
                    'status': 'OK',
                    'filename': filename,
                    'time': elapsed,
                    'throughput': throughput,
                    'size': file_size
                }
            return {'status': 'ERROR', 'data': hasil.get('data', 'Unknown error')}
        except Exception as e:
            return {'status': 'ERROR', 'data': str(e)}

    def remote_get(self, filename):
        start_time = time.time()
        command_str = f"GET {filename}"
        hasil = self.send_command(command_str)
        if hasil['status'] == 'OK':
            namafile = f"downloaded_{filename}"
            isifile = base64.b64decode(hasil['data_file'])
            with open(namafile, 'wb+') as fp:
                fp.write(isifile)
            elapsed = time.time() - start_time
            file_size = len(isifile)
            throughput = file_size / elapsed if elapsed > 0 else 0
            return {
                'status': 'OK',
                'filename': filename,
                'time': elapsed,
                'throughput': throughput,
                'size': file_size
            }
        return {'status': 'ERROR', 'data': hasil.get('data', 'Unknown error')}

    def run_operation(self, operation, filename, max_retries=10, repeat=1):
        combined_results = []
        for _ in range(repeat):
            for attempt in range(max_retries):
                if operation == 'UPLOAD':
                    result = self.remote_upload('10mb-file.pdf')
                elif operation == 'GET':
                    result = self.remote_get('10mb-file.pdf')
                else:
                    result = {'status': 'ERROR', 'data': 'Invalid operation'}
                combined_results.append(result)
                break 
        return combined_results

    def run_stress_test(self, operation, volumefile, client_workers):
        print(f"\nStarting test: {operation} {volumefile} with {client_workers} client workers")
    
        repeat = {
            '10mb': 1,
            '50mb': 5,
            '100mb': 10
        }.get(volumefile, 1)
    
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=client_workers) as executor:
            futures = [
                executor.submit(self.run_operation, operation, volumefile, repeat=repeat)
                for _ in range(client_workers)
            ]
            results_nested = [f.result() for f in futures]
    
        total_time = time.time() - start_time
        results = [item for sublist in results_nested for item in sublist] 
    
        success = sum(1 for r in results if r['status'] == 'OK') / repeat
        failed = client_workers - success
        avg_time = sum(r.get('time', 0) for r in results if r['status'] == 'OK') / success if success > 0 else 0
        total_throughput = sum(r.get('throughput', 0) for r in results if r['status'] == 'OK')
        avg_throughput = total_throughput / success if success > 0 else 0
        total_file_size = sum(r.get('size', 0) for r in results if r['status'] == 'OK')
    
        result = {
            'operation': operation,
            'volume_file': volumefile,
            'file_size': total_file_size,
            'client_workers': client_workers,
            'success': success,
            'failed': failed,
            'total_time': total_time,
            'avg_total_time_per_client': avg_time,
            'total_throughput': total_throughput,
            'avg_throughput': avg_throughput,
            'throughput_mbps': (avg_throughput / (1024 * 1024)) if avg_throughput > 0 else 0
        }
    
        self.results.append(result)
        self.save_results()
    
        print(f"Test completed: Success={success}, Failed={failed}, Time={total_time:.2f}s, Avg Time/Client={avg_time:.2f}s, Avg Total Throughput/Client={result['throughput_mbps']:.2f} MB/s")
    
    
        return result

    def save_results(self):
        with open(RESULTS_FILE, 'w', newline='') as csvfile:
            fieldnames = [
                'operation', 'volume_file', 'file_size', 'client_workers',
                'success', 'failed', 'total_time', 'avg_total_time_per_client',
                'total_throughput', 'avg_throughput', 'throughput_mbps'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.results)

    def run_all_tests(self):
        print("Starting stress tests...")
        print("Make sure your server is running at", SERVER_ADDRESS)
        
        for operation in OPERATIONS:
            for volume_size in VOLUME_SIZES:
                for client_workers in CLIENT_WORKERS:
                    self.run_stress_test(operation, volume_size, client_workers)
        
        print("\nAll tests completed. Results saved to", RESULTS_FILE)

if __name__ == '__main__':
    os.chdir('files/')
    tester = StressTester()
    tester.run_all_tests()