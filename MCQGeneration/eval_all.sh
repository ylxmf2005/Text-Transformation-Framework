#python -m seceval.eval -m Qwen_Qwen-7B -d dataset/all.json  -B local_hf -o result
#python -m seceval.eval -m mistralai_Mistral-7B-v0.1 -d  dataset/all.json  -B local_hf  -o result
#python -m seceval.eval -m microsoft_Orca-2-7b -d  dataset/all.json  -B local_hf -o result
#python -m seceval.eval -m BAAI_Aquila2-7B -d  dataset/all.json  -B local_hf -o result
#python -m seceval.eval -m NousResearch_Llama-2-7b-hf -d  dataset/all.json  -B local_hf  -o result
#python -m seceval.eval -m internlm_internlm-7b -d  dataset/all.json  -B local_hf  -o result
#python -m seceval.eval -m 01-ai_Yi-6B -d  dataset/all.json  -B local_hf -o result
#python -m seceval.eval -m THUDM_chatglm3-6b-base -d  dataset/all.json  -B local_hf  -o result
python -m seceval.eval -m gpt-35-turbo -d  dataset/all.json  -B azure  -b 10 -o result