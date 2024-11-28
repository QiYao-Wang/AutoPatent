import pandas as pd
import argparse
import nltk
from nltk.tokenize import sent_tokenize
from nltk.translate.bleu_score import SmoothingFunction, sentence_bleu
import tqdm
from rouge import Rouge
import sys
import tiktoken
from evaluate import load
import itertools
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords


# nltk.download('stopwords')
# nltk.download("punkt")

def jaccard_similarity(words1, words2):
    # 分词
    set1 = set(words1)
    set2 = set(words2)

    intersection = set1 & set2
    union = set1 | set2

    return len(intersection) / len(union) if union else 0


stop_words = set(stopwords.words('english'))
tokenizer = tiktoken.encoding_for_model("gpt-4o-mini")


def bleu(df, bleu_k=4):
    df_iter = tqdm.tqdm(df.iterrows(), total=len(df))
    bleu_avg = 0
    count = 0
    for index, row in df_iter:
        count += 1
        source_text = [row["ground_truth"]]
        target_text = row["model_output"]
        smooth = SmoothingFunction().method1
        weight = None
        if bleu_k == 1:
            weight = (1, 0, 0, 0)
        elif bleu_k == 2:
            weight = (0.5, 0.5, 0, 0)
        elif bleu_k == 3:
            weight = (1 / 3, 1 / 3, 1 / 3, 0)
        elif bleu_k == 4:
            weight = (1 / 4, 1 / 4, 1 / 4, 1 / 4)
        if weight is None:
            print("The bleu_k is ranging from 1 to 4.")
            break
        bleu_score = sentence_bleu(source_text, target_text, weights=weight, smoothing_function=smooth)
        bleu_avg = bleu_avg + bleu_score
        df_iter.set_description(f"BLEU: {bleu_avg * 100 / count:.4f}")


def rouge_(df):
    # 将递归深度限制增加，比如增加到 2000
    sys.setrecursionlimit(10000)
    # 暂时先给出 F1
    df_iter = tqdm.tqdm(df.iterrows(), total=len(df))
    rouge1_avg = 0
    rouge2_avg = 0
    rougeL_avg = 0
    count = 0
    avg_tokens = 0
    rouge = Rouge()
    tokenizer = tiktoken.encoding_for_model("gpt-4o-mini")
    for index, row in df_iter:
        count += 1
        avg_tokens += len(tokenizer.encode(row["model_output"]))
        if len(tokenizer.encode(row["model_output"])) > 40000:
            df_iter.set_description(
                f"Tokens: {avg_tokens / count:.4f}, ROUGE-1: {rouge1_avg * 100 / count:.4f}, ROUGE-2: {rouge2_avg * 100 / count:.4f}, ROUGE-L: {rougeL_avg * 100 / count:.4f}")
            continue
        source_text = row["ground_truth"]
        target_text = row["model_output"]
        scores = rouge.get_scores(source_text, target_text)
        rouge1_avg += scores[0]["rouge-1"]["f"]
        rouge2_avg += scores[0]["rouge-2"]["f"]
        rougeL_avg += scores[0]["rouge-l"]["f"]
        df_iter.set_description(
            f"Tokens: {avg_tokens / count:.4f}, ROUGE-1: {rouge1_avg * 100 / count:.4f}, ROUGE-2: {rouge2_avg * 100 / count:.4f}, ROUGE-L: {rougeL_avg * 100 / count:.4f}")


def count_avg_tokens(df):
    df_iter = tqdm.tqdm(df.iterrows(), total=len(df))
    count = 0
    avg_tokens = 0
    tokenizer = tiktoken.encoding_for_model("gpt-4o-mini")
    for index, row in df_iter:
        count += 1
        avg_tokens += len(tokenizer.encode(row["model_output"]))
        df_iter.set_description(f"Avg Tokens: {avg_tokens / count:.4f}")


def IRR(df, threshold=0.8):
    df_iter = tqdm.tqdm(df.iterrows(), total=len(df))
    re_8_list = []
    re_6_list = []
    re_4_list = []
    re_2_list = []
    for index, row in df_iter:
        re_8 = 0
        re_6 = 0
        re_4 = 0
        re_2 = 0
        model_output = row["model_output"]
        # print("====ground_truth====")
        # model_output = row["ground_truth"]
        sentences = sent_tokenize(model_output)
        pairs = [(x, y) for x, y in itertools.combinations(sentences, 2)]
        if len(pairs) == 0:
            re_8_list.append(0)  # 如果没有句子对，重复率为 0
            re_6_list.append(0)  # 如果没有句子对，重复率为 0
            re_4_list.append(0)  # 如果没有句子对，重复率为 0
            re_2_list.append(0)  # 如果没有句子对，重复率为 0
            continue
        for pair in pairs:
            sen1, sen2 = pair
            sen1 = sen1.strip()
            sen2 = sen2.strip()
            words1 = word_tokenize(sen1)
            words2 = word_tokenize(sen2)
            filtered_words1 = [word for word in words1 if word.lower() not in stop_words]
            filtered_words2 = [word for word in words2 if word.lower() not in stop_words]
            similarity = jaccard_similarity(filtered_words1, filtered_words2)
            if similarity >= 0.8:
                re_8 += 1
            if similarity >= 0.6:
                re_6 += 1
            if similarity >= 0.4:
                re_4 += 1
            if similarity >= 0.2:
                re_2 += 1
        re_8_list.append(re_8 / len(pairs))
        re_6_list.append(re_6 / len(pairs))
        re_4_list.append(re_4 / len(pairs))
        re_2_list.append(re_2 / len(pairs))

        avg_rr_8 = sum(re_8_list) / len(re_8_list)
        avg_rr_6 = sum(re_6_list) / len(re_6_list)
        avg_rr_4 = sum(re_4_list) / len(re_4_list)
        avg_rr_2 = sum(re_2_list) / len(re_2_list)
        df_iter.set_description(
            f"IRR(0.8):{100 * (1 - avg_rr_8):.4f}, IRR(0.6): {100 * (1 - avg_rr_6):.4f}, IRR(0.4): {100 * (1 - avg_rr_4):.4f}, IRR(0.2): {100 * (1 - avg_rr_2):.4f}")


# CUDA_VISIBLE_DEVICES=7 python metric.py --dataset /home/wangqiyao/draft2Patent/baseline/gpt-4o-mini/draft2Patent/
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, default=None)
    parser.add_argument("--metric", type=str, default="BLEU")
    parser.add_argument("--bleu_k", type=int, default=4)
    parser.add_argument("--threshold", type=float, default=0.8)
    args = parser.parse_args()
    if args.dataset is None:
        print("Please provide a dataset's absolute path.")
    else:
        data_df = pd.read_json(args.dataset)
        if args.metric == "all":
            bleu(data_df, bleu_k=args.bleu_k)
            rouge_(data_df)
            count_avg_tokens(data_df)
            IRR(data_df, threshold=args.threshold)
        elif args.metric == "BLEU":
            bleu(data_df, bleu_k=args.bleu_k)
        elif args.metric == "ROUGE":
            rouge_(data_df)
        elif args.metric == "Token":
            count_avg_tokens(data_df)
        elif args.metric == "IRR":
            IRR(data_df, threshold=args.threshold)
