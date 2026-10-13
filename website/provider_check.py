"""Safe provider diagnostics. Model listing is not an inference quality test."""
import os
import requests


def check_provider(live=False):
    base=os.environ.get('SILICONFLOW_BASE_URL','https://api.siliconflow.cn/v1').rstrip('/')
    key=os.environ.get('SILICONFLOW_API_KEY','')
    result={'base_url':base,'model':os.environ.get('SILICONFLOW_MODEL','Qwen/Qwen3.5-122B-A10B'),
            'key_present':bool(key) and key not in ('CHANGE_ME','你的 SiliconFlow 密钥'),
            'automatic_writing_enabled':os.environ.get('BOOKSITE_AUTO_WRITE')=='1',
            'live_model_verified':False,'inference_tested':False,'price_verified':False}
    if not live:
        result['status']='configuration_only'
        return result
    if not result['key_present']:
        result['status']='missing_key'
        return result
    if base!='https://api.siliconflow.cn/v1':
        result['status']='unsupported_endpoint'
        return result
    try:
        response=requests.get(base+'/models',headers={'Authorization':'Bearer '+key},timeout=(10,30),allow_redirects=False)
        result['http_status']=response.status_code
        if response.status_code==200:
            data=response.json()['data']
            result['live_model_verified']=any(item.get('id')==result['model'] for item in data)
            result['status']='model_listed' if result['live_model_verified'] else 'model_not_listed'
        else:
            result['status']='http_error'
    except requests.RequestException:
        result['status']='network_error'
    except (ValueError,KeyError,TypeError,AttributeError):
        result['status']='invalid_model_inventory'
    return result
