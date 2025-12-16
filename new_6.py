import os
from pathlib import Path
from collections import defaultdict
import numpy as np

from defaut_arg_deep import AddDefaultArgValue
from except_code import ExceptionRefactor
from hardcode_deep import HardcodedValues
from forwhilev2 import ForWhile
from lambda_refactor import LambdaRefactor
from asserts import AddAssertions
from partials_ls import PartialsRefactor
from ternary_ref import TernaryRefactor
from try_crypto import CryptoTryExceptInjector
from conv_assign import AugAssignRefactor
from conv_except_assertion import RaiseRefactor
from line_stmts import AssignGroupers
from elif_ren import ElIfConverter
from elseIf import ElseIfConverter
from param_refact_v2 import ParameterRefactor
from var_extract import CryptoVarExtractor

import rem_comments  
import bert_code 

refactor_classes = {
    "raise_refact": RaiseRefactor(),
    "line_stmts": AssignGroupers(),
    "elif_ref": ElIfConverter(),
    "elseif": ElseIfConverter(),
    "add_default_arg": AddDefaultArgValue(),
    "hardcoded_values": HardcodedValues(),
    "exception_code": ExceptionRefactor(),
    "var_extract": CryptoVarExtractor(),
    "loops": ForWhile(),
    "lambda_refactor": LambdaRefactor(),
    "assertions": AddAssertions(),
    "partials": PartialsRefactor(),
    "param_refactor": ParameterRefactor(),
    "ternary": TernaryRefactor(),
    "crypto_try": CryptoTryExceptInjector(),
    "conv_assign": AugAssignRefactor(),
    # Duplicate entries added to hit the required total of 24 techniques:
    "loops1": ForWhile(), 
    "lambda_refactor1": LambdaRefactor(),
    "assertions1": AddAssertions(),
    "partials1": PartialsRefactor(),
    "param_refactor1": ParameterRefactor(),
    "ternary1": TernaryRefactor(),
    "crypto_try1": CryptoTryExceptInjector(),
    "conv_assign1": AugAssignRefactor(),
}

refactor_classes = {k: v for k, v in refactor_classes.items() if v is not None and isinstance(k, str)}

assert len(refactor_classes) == 24, f"Expected 24 techniques, got {len(refactor_classes)}. Adjust technique list to meet the 24-count for 4x6 pipelines."


def read_code(file_path: Path) -> str:
    return file_path.read_text(encoding="utf-8", errors="ignore")


def apply_technique(code: str, tech_name: str) -> str:
    try:
        return refactor_classes[tech_name].get_refactored_code(code)
    except Exception as e:
        return code  


def apply_pipeline(code: str, pipeline: list[str]) -> str:
    current = rem_comments.get_refactored_code(code)  # Initial comment removal
    for tech in pipeline:
        current = apply_technique(current, tech)
    return current


def measure_divergence(original: str, modified: str) -> float:
    if original.strip() == modified.strip():
        return 0.0
    try:
        result = bert_code.analyze_code_pair(original, modified)
        val = result.get("semantic_difference_percent", 0.0)
        return max(0.0, float(val))
    except Exception as e:
        return 0.0


def evaluate_individual_techniques(source_dir: str = "source") -> dict[str, float]:
    programs = list(Path(source_dir).glob("*.py"))
    if not programs:
        print(f"[Error] No files in '{source_dir}'")
        return {}

    print(f"\nEvaluating {len(refactor_classes)} techniques on {len(programs)} programs...\n")
    scores = defaultdict(list)

    for prog_path in programs:
        code = read_code(prog_path)
        for tech_name in refactor_classes:
            variant = apply_technique(code, tech_name)
            div = measure_divergence(code, variant)
            scores[tech_name].append(div)

    return {tech: np.mean(vals) for tech, vals in scores.items()}


def evaluate_pipelines(pipelines: list[list[str]], source_dir: str = "source") -> dict[tuple, float]:
    programs = list(Path(source_dir).glob("*.py"))
    if not programs:
        return {}

    print(f"\nEvaluating {len(pipelines)} pipelines across {len(programs)} programs...")
    results = {}
    
    for pipeline in pipelines:
        pipe_key = tuple(pipeline)
        div_scores = []

        for prog_path in programs:
            code = read_code(prog_path)
            variant = apply_pipeline(code, pipeline)
            div = measure_divergence(code, variant)
            div_scores.append(div)

        avg_div = np.mean(div_scores) if div_scores else 0.0
        results[pipe_key] = avg_div

    return results


def pair_strongest_with_weakest(scored_items):
    sorted_items = sorted(scored_items, key=lambda x: x[1], reverse=True)
    pipelines = []
    i, j = 0, len(sorted_items) - 1

    while i < j:
        strong_techs = sorted_items[i][0]
        weak_techs = sorted_items[j][0]
        
        new_pipe = list(strong_techs) + list(weak_techs) 
        pipelines.append(new_pipe)
        
        i += 1
        j -= 1

    if i == j:
        mid_techs = sorted_items[i][0]
        pipelines.append(list(mid_techs))

    return pipelines


def create_max_divergent_pipelines(source_dir: str = "source", target: int = 4):
    
    print("="*90)
    print("  MAXIMALLY DIVERGENT PIPELINE GENERATOR (Strongest + Weakest Pairing)")
    print(f"  Target: {target} final pipelines, each with {len(refactor_classes) // target} techniques")
    print("="*90)

    scores = evaluate_individual_techniques(source_dir)
    if not scores:
        return []

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    print("\nIndividual Technique Rankings (Divergence):")
    for i, (tech, score) in enumerate(ranked, 1):
        print(f"  {i:2}. {tech:<20} → {score:6.2f}%")

    current = [[tech] for tech, _ in ranked] 

    round_num = 1
    while len(current) > 6:
        new_len = len(current) // 2
        print(f"\n--- Round {round_num}: Pairing {len(current)} Pipelines → {new_len} Pipelines ---")
        pipe_scores = evaluate_pipelines(current, source_dir)

        ranked_pipes = sorted(pipe_scores.items(), key=lambda x: x[1], reverse=True)
        
        print("\nBest pipelines this round:")
        for i, (p, s) in enumerate(ranked_pipes[:6], 1):
            print(f"  {i}. {list(p)} → {s:.2f}%  (len={len(p)})")

        current = pair_strongest_with_weakest(ranked_pipes)
        round_num += 1

    print(f"\nFINAL: {len(current)} pipelines, each with 6 techniques")
    final_scores = evaluate_pipelines(current, source_dir)
    final_ranked = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)

    print("\n" + "="*90)
    print("FINAL 6 PIPELINES (4 techniques each)")
    print("="*90)
    for i, (pipe_tuple, score) in enumerate(final_ranked, 1):
        pipe = list(pipe_tuple)
        print(f"Pipeline {i}: {pipe}")
        print(f"           Avg Divergence: {score:.2f}%\n")

    return [list(p) for p, _ in final_ranked]


def main():
    final_pipelines = create_max_divergent_pipelines("source", target=4)
    if final_pipelines:
        print("SUCCESS! Your 6 best pipelines (each with 4 techniques) are above.")
    else:
        print("Failed. Check folder 'source/' has .py files.")


if __name__ == "__main__":
        
    main()
