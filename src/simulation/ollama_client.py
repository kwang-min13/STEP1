"""
Ollama Client Module

Ollama API 연동을 위한 클라이언트
"""

import requests
import json
from typing import Optional, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OllamaClient:
    """Ollama API 클라이언트"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        """
        초기화
        
        Args:
            base_url: Ollama 서버 URL
            model: 사용할 모델 이름
        """
        self.base_url = base_url
        self.model = model
    
    def generate(self, prompt: str, temperature: float = 0.7) -> Optional[str]:
        """
        텍스트 생성
        
        Args:
            prompt: 입력 프롬프트
            temperature: 생성 온도 (0.0-1.0)
            
        Returns:
            생성된 텍스트 또는 None
        """
        try:
            url = f"{self.base_url}/api/generate"
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature
                }
            }
            
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', '').strip()
            
        except requests.exceptions.ConnectionError:
            logger.error("Ollama 서버에 연결할 수 없습니다. Ollama가 실행 중인지 확인하세요.")
            return None
        except requests.exceptions.Timeout:
            logger.error("요청 시간 초과")
            return None
        except Exception as e:
            logger.error(f"생성 실패: {str(e)}")
            return None
    
    def check_connection(self) -> bool:
        """Ollama 서버 연결 확인"""
        try:
            url = f"{self.base_url}/api/tags"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except:
            return False


if __name__ == "__main__":
    # 테스트
    client = OllamaClient()
    
    if client.check_connection():
        logger.info("✓ Ollama 서버 연결 성공")
        
        # 간단한 테스트
        response = client.generate("Say hello in one sentence.")
        if response:
            logger.info(f"응답: {response}")
    else:
        logger.warning("✗ Ollama 서버에 연결할 수 없습니다.")
        logger.info("Ollama를 설치하고 실행하세요: https://ollama.ai")
