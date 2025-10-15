#!/usr/bin/env python3
"""
WebSocket Connection Monitor - Real-time monitoring of WebSocket performance
Usage: python websocket_monitor.py
"""

import asyncio
import websockets
import json
import time
import logging
from datetime import datetime

# Configuration
WS_BASE_URL = "ws://localhost:8000"
JWT_TOKEN = "your_jwt_token_here"  # Replace with actual JWT token

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WebSocketMonitor:
    def __init__(self):
        self.connections = {}
        self.stats = {
            'total_connections': 0,
            'active_connections': 0,
            'failed_connections': 0,
            'timeouts': 0,
            'messages_sent': 0,
            'messages_received': 0
        }
    
    async def monitor_connection(self, ws_url, connection_name, test_messages):
        """Monitor a single WebSocket connection"""
        connection_id = f"{connection_name}_{int(time.time())}"
        start_time = time.time()
        
        try:
            self.stats['total_connections'] += 1
            logger.info(f"🔗 [{connection_id}] Connecting to {connection_name}...")
            
            # Connect with timeout
            ws = await asyncio.wait_for(
                websockets.connect(ws_url, ping_interval=20, ping_timeout=10),
                timeout=10.0
            )
            
            self.stats['active_connections'] += 1
            self.connections[connection_id] = {
                'ws': ws,
                'start_time': start_time,
                'name': connection_name
            }
            
            connect_time = time.time() - start_time
            logger.info(f"✅ [{connection_id}] Connected in {connect_time:.2f}s")
            
            # Send test messages
            for i, message in enumerate(test_messages):
                try:
                    self.stats['messages_sent'] += 1
                    await ws.send(json.dumps(message))
                    logger.info(f"📤 [{connection_id}] Sent: {message.get('type', 'unknown')}")
                    
                    # Wait for response with timeout
                    response = await asyncio.wait_for(ws.recv(), timeout=15.0)
                    self.stats['messages_received'] += 1
                    
                    data = json.loads(response)
                    response_time = time.time() - start_time
                    
                    if data.get('type') == 'error':
                        logger.error(f"❌ [{connection_id}] Error response: {data.get('message')}")
                    else:
                        logger.info(f"📨 [{connection_id}] Received: {data.get('type', 'unknown')} in {response_time:.2f}s")
                    
                    # Small delay between messages
                    await asyncio.sleep(0.5)
                    
                except asyncio.TimeoutError:
                    self.stats['timeouts'] += 1
                    logger.warning(f"⏰ [{connection_id}] Timeout on message {i+1}")
                    break
                except Exception as e:
                    logger.error(f"❌ [{connection_id}] Message error: {e}")
                    break
            
            # Keep connection alive for monitoring
            logger.info(f"🔄 [{connection_id}] Monitoring connection...")
            await asyncio.sleep(30)  # Monitor for 30 seconds
            
            # Close gracefully
            await ws.close()
            logger.info(f"✅ [{connection_id}] Closed gracefully")
            
        except asyncio.TimeoutError:
            self.stats['timeouts'] += 1
            self.stats['failed_connections'] += 1
            logger.error(f"⏰ [{connection_id}] Connection timeout")
        except Exception as e:
            self.stats['failed_connections'] += 1
            logger.error(f"❌ [{connection_id}] Connection failed: {e}")
        finally:
            if connection_id in self.connections:
                self.stats['active_connections'] -= 1
                del self.connections[connection_id]
    
    async def continuous_monitoring(self):
        """Run continuous monitoring of all WebSocket types"""
        test_configs = [
            {
                'url': f"{WS_BASE_URL}/ws/customers/?token={JWT_TOKEN}",
                'name': 'customers',
                'messages': [
                    {"type": "get_customers"},
                    {"type": "filter_customers", "filters": {"search": "test"}}
                ]
            },
            {
                'url': f"{WS_BASE_URL}/ws/conversations/?token={JWT_TOKEN}",
                'name': 'conversations', 
                'messages': [
                    {"type": "get_conversations"},
                    {"type": "filter_conversations", "filters": {"status": "open"}}
                ]
            }
        ]
        
        logger.info("🚀 Starting continuous WebSocket monitoring...")
        
        while True:
            try:
                # Start monitoring tasks for each WebSocket type
                tasks = []
                for config in test_configs:
                    task = asyncio.create_task(
                        self.monitor_connection(
                            config['url'],
                            config['name'],
                            config['messages']
                        )
                    )
                    tasks.append(task)
                
                # Wait for all tasks to complete
                await asyncio.gather(*tasks, return_exceptions=True)
                
                # Print stats
                self.print_stats()
                
                # Wait before next monitoring cycle
                logger.info("⏸️  Waiting 60 seconds before next cycle...")
                await asyncio.sleep(60)
                
            except KeyboardInterrupt:
                logger.info("👋 Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"💥 Monitoring error: {e}")
                await asyncio.sleep(10)
    
    def print_stats(self):
        """Print connection statistics"""
        logger.info("📊 Connection Statistics:")
        logger.info(f"   Total Connections: {self.stats['total_connections']}")
        logger.info(f"   Active Connections: {self.stats['active_connections']}")
        logger.info(f"   Failed Connections: {self.stats['failed_connections']}")
        logger.info(f"   Timeouts: {self.stats['timeouts']}")
        logger.info(f"   Messages Sent: {self.stats['messages_sent']}")
        logger.info(f"   Messages Received: {self.stats['messages_received']}")
        
        success_rate = 0
        if self.stats['total_connections'] > 0:
            success_rate = ((self.stats['total_connections'] - self.stats['failed_connections']) / 
                          self.stats['total_connections']) * 100
        
        logger.info(f"   Success Rate: {success_rate:.1f}%")
        logger.info("   " + "="*50)

async def quick_test():
    """Run a quick test of all WebSocket endpoints"""
    monitor = WebSocketMonitor()
    
    print("🧪 Quick WebSocket Test")
    print("="*50)
    
    if JWT_TOKEN == "your_jwt_token_here":
        print("⚠️  Please set a valid JWT_TOKEN in the script")
        return
    
    test_configs = [
        {
            'url': f"{WS_BASE_URL}/ws/customers/?token={JWT_TOKEN}",
            'name': 'customers',
            'messages': [{"type": "get_customers"}]
        },
        {
            'url': f"{WS_BASE_URL}/ws/conversations/?token={JWT_TOKEN}",
            'name': 'conversations',
            'messages': [{"type": "get_conversations"}]
        }
    ]
    
    tasks = []
    for config in test_configs:
        task = asyncio.create_task(
            monitor.monitor_connection(
                config['url'],
                config['name'],
                config['messages']
            )
        )
        tasks.append(task)
    
    await asyncio.gather(*tasks, return_exceptions=True)
    monitor.print_stats()

def main():
    """Main function"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "monitor":
        # Continuous monitoring mode
        monitor = WebSocketMonitor()
        try:
            asyncio.run(monitor.continuous_monitoring())
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped")
    else:
        # Quick test mode
        try:
            asyncio.run(quick_test())
        except KeyboardInterrupt:
            print("\n👋 Test interrupted")

if __name__ == "__main__":
    main()