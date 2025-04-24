import openai
import time
import yaml
import json
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
from typing import Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

class OpenAIBenchmark:
    def __init__(self, config_path: str = "config.yaml", max_workers: int = 3):
        """初始化基准测试工具
        
        Args:
            config_path (str): 配置文件路径
            max_workers (int): 最大并发线程数
        """
        self.max_workers = max_workers
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # 检查provider名称是否重复
        provider_names = [p['name'] for p in self.config['providers']]
        if len(provider_names) != len(set(provider_names)):
            duplicates = {name for name in provider_names if provider_names.count(name) > 1}
            raise ValueError(f"发现重复的provider名称: {', '.join(duplicates)}")
        
        self.clients = {}
        for provider in self.config['providers']:
            self.clients[provider['name']] = openai.OpenAI(
                api_key=provider['api_key'],
                base_url=provider.get('base_url')
            )
        
    
    def _count_tokens(self, text: str) -> int:
        """简单估算token数量 (实际应使用tiktoken库)
        
        Args:
            text (str): 输入文本
            
        Returns:
            int: 估算的token数量
        """
        return len(text) // 4  # 近似估算
    
    def _test_single_model(self, provider_name: str, model_name: str, params: Dict) -> Tuple[float, int, str]:
        """测试单个模型性能
        
        Args:
            provider_name (str): 服务商名称
            model_name (str): 模型名称
            params (Dict): 模型参数
            
        Returns:
            Tuple[float, int, str]: (tokens/s速度, 总token数, API响应内容)
        """
        client = self.clients[provider_name]
        prompt = self.config['test_prompt']
        
        # 开始计时
        start_time = time.perf_counter()
        
        # 调用OpenAI API
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            **params
        )
        
        # 计算耗时
        duration = time.perf_counter() - start_time
        
        # 计算token数量
        prompt_tokens = self._count_tokens(prompt)
        completion_tokens = self._count_tokens(response.choices[0].message.content)
        total_tokens = prompt_tokens + completion_tokens
        
        # 计算tokens/s
        speed = total_tokens / duration
        
        return speed, total_tokens, response.choices[0].message.content
    
    def _save_log(self, results: Dict[str, Dict], responses: Dict[str, str]):
        """保存JSON格式的测试日志
        
        Args:
            results (Dict[str, Dict]): 测试结果数据
            responses (Dict[str, str]): API响应内容
        """
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "responses": responses
        }
        
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n测试日志已保存到: {log_file}")
    
    def run_benchmark(self) -> Dict[str, Dict]:
        """运行所有模型的基准测试
        
        Returns:
            Dict[str, Dict]: 测试结果 {模型名: {速度, token数, 状态}}
        """
        results = {}
        # 收集所有模型测试任务
        test_tasks = []
        for provider in self.config['providers']:
            for model in provider['models']:
                test_tasks.append({
                    'provider': provider['name'],
                    'model_name': model['name'],
                    'params': model['params']
                })
        
        print(f"开始测试 {len(test_tasks)} 个模型(最大并发数: {self.max_workers})...")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(
                    self._test_single_model,
                    task['provider'],
                    task['model_name'],
                    task['params']
                ): f"{task['provider']}/{task['model_name']}"
                for task in test_tasks
            }
            
            for future in tqdm(as_completed(futures), total=len(futures)):
                model_name = futures[future]
                try:
                    speed, tokens, response = future.result()
                    results[model_name] = {
                        'speed': round(speed, 2),
                        'tokens': tokens,
                        'status': 'success',
                        'response': response
                    }
                except Exception as e:
                    results[model_name] = {
                        'speed': 0,
                        'tokens': 0,
                        'status': f'failed: {str(e)}'
                    }
        
        # 保存测试日志
        responses = {
            model: data.get('response', '')
            for model, data in results.items()
            if data['status'] == 'success'
        }
        self._save_log(results, responses)
        
        return results
    
    def print_results(self, results: Dict[str, Dict]):
        """打印测试结果
        
        Args:
            results (Dict[str, Dict]): 测试结果
        """
        print("\n=== 测试结果 ===")
        print(f"{'模型':<20} {'速度(tokens/s)':<15} {'总token数':<10} 状态")
        print("-" * 60)
        
        for model, data in results.items():
            print(f"{model:<20} {data['speed']:<15.2f} {data['tokens']:<10} {data['status']}")

if __name__ == "__main__":
    try:
        benchmark = OpenAIBenchmark(max_workers=4)  # 增加默认并发数
        results = benchmark.run_benchmark()
        benchmark.print_results(results)
    except ValueError as e:
        print(f"配置错误: {e}")
        exit(1)