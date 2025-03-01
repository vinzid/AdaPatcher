from dataclasses import dataclass, field
from typing import Dict, Optional, Sequence, List
import json
import os
from utils.arguments import train_config
import torch
from torch.utils.data import DistributedSampler
from Model.model import LoraCodeLlama
from torch.utils.data import DataLoader
from utils.train_utils import train, clear_gpu_cache, setup_environ_flags
import torch.distributed as dist
from peft import get_peft_model, PeftModel
from configs.config_utils import generate_peft_config
from transformers import (
    LlamaForCausalLM,
    LlamaTokenizer
)
from utils.load_data import processClass
import transformers 
#import deepspeed
#deepspeed.ops.op_builder.CPUAdamBuilder().load()
from tqdm import tqdm
from codeTool.utlis.utils import save_data_to_json
import re
import inspect
from transformers import GenerationConfig
#import safetensors
#safetensors_rust.set_header_size_limit(1024 * 1024)  # 设置头部大小限制为 1MB

B_INST, E_INST = "[INST]", "[/INST]"
B_SYS, E_SYS = "<<SYS>>\n", "\n<</SYS>>\n\n"

def load_peft_model(model, peft_model):
    peft_model = PeftModel.from_pretrained(model, peft_model)
    return peft_model

def extract_triple_quotes(text):
    pattern = r"```(.*?)```"
    matches = re.findall(pattern, text, flags=re.DOTALL) 
    if matches:
        return matches[0]
    else:
        return text
    
def Get_code_content(text):
    text = text.split(E_INST)[1]   
    code_content = extract_triple_quotes(text)
    return code_content

def eval_for_use_peft(args, model, tokenizer, dataloader):
    model.eval()
    eval_list = []
    for step, batch in enumerate(tqdm(dataloader,colour="green", desc="predict Epoch", dynamic_ncols=True)): 
        input_ids=batch['input_ids'].cuda()
        user_id_batch=batch['user_id_batch']
        problem_id_batch=batch['problem_id_batch']
        submission1_id_batch=batch['submission1_id_list']
        with torch.no_grad():
            output_sequences = model.generate(input_ids=input_ids, max_new_tokens= (args.max_length/2), \
                                              do_sample= True, top_p=0.9, num_return_sequences = 3, pad_token_id = tokenizer.pad_token_id, use_cache=True)
        #print(output_sequences.shape)
        for i in range(0, 6):
            generated_text = tokenizer.decode(output_sequences[i], skip_special_tokens=True)
            print(generated_text)
        #input()
        for i in range(0, args.per_device_eval_batch_size):
            generated_text = tokenizer.decode(output_sequences[i], skip_special_tokens=True)
            user_id = user_id_batch[i]
            problem_id = problem_id_batch[i]
            submission1_id = submission1_id_batch[i]
            code_content = Get_code_content(generated_text)
            item = {"user_id":user_id, "problem_id":problem_id, "submission1_id":submission1_id, "code_content": code_content, "origin_generated_text": generated_text.split(E_INST)[1]}
            eval_list.append(item)
    save_filePath =  args.predict_dir + f"checkpoint-7400_test.json"
    save_data_to_json(eval_list, save_filePath)

def main(**kwargs):

    dist.init_process_group("nccl")
    parser = transformers.HfArgumentParser(train_config)
    args = parser.parse_args_into_dataclasses()[0]
    #print(args)
    #input()

    # Set the seeds for reproducibility
    torch.cuda.manual_seed(args.seed)
    torch.manual_seed(args.seed)
    
    # torchrun specific
    local_rank = int(os.environ["LOCAL_RANK"])
    rank = int(os.environ["RANK"])
    world_size = int(os.environ["WORLD_SIZE"])
    if torch.distributed.is_initialized():
        torch.cuda.set_device(local_rank)
        clear_gpu_cache(local_rank)
        setup_environ_flags(rank)

    # inint model
    #---------------------------------------------------------------------------------
    
    
    if args.use_peft == True:

        model = LlamaForCausalLM.from_pretrained(args.output_dir)
        tokenizer = LlamaTokenizer.from_pretrained(args.output_dir, padding_side='left')#, padding_side='left'
        model.resize_token_embeddings(len(tokenizer))
        model = model.cuda()
        print(f"Model embedding size: {model.get_input_embeddings().weight.size(0)}")
        print(f"Tokenizer vocabulary size: {len(tokenizer)}")
        default_generation_config = model.generation_config
        print("Default build configuration parameters for the model:")
        for param, value in vars(default_generation_config).items():
            print(f"{param}: {value}")

        # Gets the signature of the generate method
        generate_signature = inspect.signature(model.generate)
        print("\nmodel.generate the parameters of the generate method (including the parameters for the default values):")
        for param in generate_signature.parameters.values():
            if param.default != inspect.Parameter.empty:
                print(f"{param.name}: {param.default}")
            else:
                print(f"{param.name}: No default value")
    else:  
            model = LlamaForCausalLM.from_pretrained(
                args.model_name_or_path,
            )
            peft_config = generate_peft_config(args, kwargs)
            model = get_peft_model(model, peft_config)
            model.resize_token_embeddings(len(tokenizer))
            print(f"Model embedding size: {model.get_input_embeddings().weight.size(0)}")
            print(f"Tokenizer vocabulary size: {len(tokenizer)}")
            model = LoraCodeLlama(model).cuda()


    # load data
    #---------------------------------------------------------------------------------  
    proc = processClass()
    eval_dataset_set = proc.get_dataset(args,tokenizer,  "test", is_test = True,rank = rank)
    val_sampler = None

    if args.do_eval:
        val_sampler = DistributedSampler(
            eval_dataset_set,
            rank=dist.get_rank(),
            num_replicas=dist.get_world_size(),
        )
    
    eval_dataloader = DataLoader(eval_dataset_set , batch_size=args.per_device_eval_batch_size, collate_fn=eval_dataset_set.collate_batch, num_workers=4,sampler=val_sampler if val_sampler else None)

    if args.use_peft:
        eval_for_use_peft(args, model,tokenizer, eval_dataloader)

        
if __name__ == "__main__":
    main()