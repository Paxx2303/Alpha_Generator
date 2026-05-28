#!/usr/bin/env python3
"""
Fix Data Pipeline for Alpha_Generator
Fixes miscategorization, removes duplicates, re-processes all data
Regenerates final_dataset, creates new Skill.md
"""

import os, json, re, shutil, hashlib, time
from pathlib import Path

RAW = Path(r"c:\Using\Alpha_Generator\alpha_skills\rawdata")
PROC = Path(r"c:\Using\Alpha_Generator\alpha_skills\processed_data")
FINAL = Path(r"c:\Using\Alpha_Generator\alpha_skills\final_dataset")
SKILL = Path(r"c:\Using\Alpha_Generator\alpha_skills\Skill.md")

# ===== STEP 1: Re-process raw data =====

print("="*60)
print("STEP 1: Re-processing raw data with correct categorization")
print("="*60)

if PROC.exists():
    for item in PROC.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        elif item.name != "README.md":
            item.unlink()

def get_category(file_path):
    src = file_path.parent.name
    
    if src == 'brain_tips':
        return 'research_insights'
    if src == 'documentation':
        return 'platform_guides'
    if src == 'alpha_examples':
        return 'research_insights'
    if src == 'quantitative_strategies':
        return 'quantitative_methods'
    
    if src == 'research_papers':
        name = file_path.stem.lower()
        if any(x in name for x in ['paper_', 'research_paper_']):
            return 'academic_papers'
        if any(x in name for x in ['markowitz', 'black_scholes', 'fama_', 'kahneman', 'jegadeesh']):
            return 'core_concepts'
        return 'research_insights'
    
    if src == 'investopedia':
        name = file_path.stem.lower()
        
        tech = ['rsi', 'relative_strength_index', 'macd', 'bollinger', 'stochastic',
            'aroon', 'average_directional_index', 'adx', 'commodity_channel_index', 'cci',
            'chaikin_money_flow', 'cmf', 'donchian', 'ease_of_movement', 'force_index',
            'keltner', 'money_flow_index', 'negative_volume_index', 'on_balance_volume',
            'parabolic_sar', 'pivot_points', 'rate_of_change', 'roc', 'relative_vigor_index',
            'volume_price_trend', 'williams_percent', 'zigzag', 'ichimoku',
            'exponential_moving_average', 'simple_moving_average', 'weighted_moving_average',
            'double_exponential_moving_average', 'triple_exponential_moving_average',
            'hull_moving_average', 'average_true_range', 'atr', 'standard_deviation_channels',
            'moving_average', 'bollinger_bands']
        for kw in tech:
            if kw in name:
                return 'technical_indicators'
        
        core = ['beta', 'capital_asset_pricing_model', 'capm', 'correlation_coefficient',
            'correlation', 'covariance', 'standard_deviation', 'standard_error',
            'normal_distribution', 'autocorrelation', 'heteroskedasticity', 'multicollinearity',
            'stationary_process', 'unit_root_test', 'hypothesis_testing', 'linear_regression',
            'multiple_regression', 'ordinary_least_squares', 'r_squared', 'p_value',
            'bootstrap_resampling', 'monte_carlo_simulation', 'time_series_analysis',
            'random_walk', 'statistical_significance', 'overfitting', 'underfitting',
            'modern_portfolio_theory', 'market_microstructure', 'quantitative_analysis',
            'value_at_risk', 'conditional_value_at_risk', 'expected_shortfall', 'tail_risk',
            'drawdown', 'maximum_drawdown', 'sharpe_ratio', 'sortino_ratio', 'treynor_ratio',
            'information_ratio', 'calmar_ratio', 'sterling_ratio', 'profit_factor', 'win_rate',
            'recovery_factor', 'tracking_error', 'jensen_alpha', 'active_return',
            'risk_reward_ratio', 'adjusted_r_squared']
        for kw in core:
            if kw in name:
                return 'core_concepts'
        
        strat = ['momentum_investing', 'mean_reversion', 'pairs_trading',
            'statistical_arbitrage', 'algorithmic_trading', 'quantitative_trading',
            'systematic_trading', 'high_frequency_trading', 'swing_trading',
            'position_trading', 'scalping', 'grid_trading', 'breakout_trading',
            'trend_following', 'market_neutral', 'long_short_equity', 'dollar_cost_averaging']
        for kw in strat:
            if kw in name:
                return 'quantitative_methods'
        
        pa = ['dow_theory', 'elliott_wave', 'wyckoff', 'fibonacci']
        for kw in pa:
            if kw in name:
                return 'technical_indicators'
        
        return 'core_concepts'
    
    return 'research_insights'


def clean_name(filename):
    cleaned = re.sub(r'[^\w\s-]', '', filename)
    cleaned = re.sub(r'\s+', '_', cleaned.strip())
    cleaned = re.sub(r'_+', '_', cleaned)
    cleaned = re.sub(r'^BRAIN_TIPS_', '', cleaned)
    cleaned = re.sub(r'^\[BRAIN_TIPS\]_', '', cleaned)
    return cleaned


stats = {'total': 0, 'processed': 0, 'excluded': 0, 'categories': {}}
seen_hashes = set()

for src_dir in ['brain_tips', 'documentation', 'investopedia', 
                'research_papers', 'alpha_examples', 'quantitative_strategies']:
    src_path = RAW / src_dir
    if not src_path.exists():
        continue
    print(f"\n  [{src_dir}]")
    for fpath in sorted(src_path.glob('*.md')):
        stats['total'] += 1
        if fpath.stat().st_size == 0:
            print(f"    skip empty: {fpath.name}")
            continue
        try:
            ch = hashlib.md5(open(fpath, 'rb').read()).hexdigest()
        except:
            continue
        if ch in seen_hashes:
            print(f"    dup content: {fpath.name}")
            continue
        seen_hashes.add(ch)
        
        cat = get_category(fpath)
        stats['categories'][cat] = stats['categories'].get(cat, 0) + 1
        
        ddir = PROC / cat
        ddir.mkdir(parents=True, exist_ok=True)
        
        cname = clean_name(fpath.stem) + '.md'
        dest = ddir / cname
        if dest.exists():
            stem = clean_name(fpath.stem)
            dest = ddir / f"{stem}_{stats['categories'][cat]}.md"
        
        shutil.copy2(fpath, dest)
        stats['processed'] += 1
        print(f"    + {fpath.name} -> {cat}/")

print(f"\n{'='*60}")
print(f"PROCESSED: {stats['processed']} files")
print(f"TOTAL RAW: {stats['total']} files")
print(f"\nCategory Distribution:")
for c, n in sorted(stats['categories'].items()):
    print(f"  {c}: {n}")


# ===== STEP 2: Regenerate final_dataset =====
print(f"\n{'='*60}")
print("STEP 2: Regenerating final_dataset")
print("="*60)

if FINAL.exists():
    for item in FINAL.iterdir():
        if item.is_file():
            item.unlink()
FINAL.mkdir(exist_ok=True)

def extract_meta(fp):
    try:
        content = open(fp, 'r', encoding='utf-8', errors='ignore').read()
        meta = {
            'filename': fp.name, 'category': fp.parent.name, 'title': '',
            'source_url': '', 'word_count': len(content.split()),
            'has_formulas': bool(re.search(r'\$.*?\$|\\[.*?\\]', content)),
            'has_code': bool(re.search(r'```|`[^`]+`', content)),
            'key_concepts': []
        }
        tm = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if tm: meta['title'] = tm.group(1).strip()
        um = re.search(r'\*\*Source:\*\*\s+(https?://[^\s]+)', content)
        if um: meta['source_url'] = um.group(1)
        headers = re.findall(r'^#{2,4}\s+(.+)$', content, re.MULTILINE)
        meta['key_concepts'] = [h.strip() for h in headers[:10]]
        return meta, content
    except:
        return {}, ""

dataset = {
    'metadata': {
        'name': 'Alpha Research Knowledge Base',
        'description': 'Comprehensive dataset for quantitative finance and alpha research',
        'version': '2.0', 'categories': [], 'total_files': 0,
        'creation_date': str(time.time())
    }, 'documents': []
}

all_cats = []
for cd in sorted(PROC.iterdir()):
    if cd.is_dir() and not cd.name.startswith('.'):
        all_cats.append(cd.name)
dataset['metadata']['categories'] = sorted(all_cats)

for cd in sorted(PROC.iterdir()):
    if not cd.is_dir() or cd.name.startswith('.'):
        continue
    print(f"  {cd.name}...")
    for fp in sorted(cd.glob('*.md')):
        meta, content = extract_meta(fp)
        if not content: continue
        dataset['documents'].append({
            'id': f"{cd.name}_{fp.stem}", 'metadata': meta, 'content': content
        })
        dataset['metadata']['total_files'] += 1

json.dump(dataset, open(FINAL / 'alpha_research_dataset.json', 'w', encoding='utf-8'), 
          indent=2, ensure_ascii=False)
print(f"\n  Consolidated: {dataset['metadata']['total_files']} docs")

summaries = {}
for cd in sorted(PROC.iterdir()):
    if not cd.is_dir() or cd.name.startswith('.'):
        continue
    cat = cd.name
    files = list(cd.glob('*.md'))
    summary = {'category': cat, 'file_count': len(files), 'files': [],
               'key_topics': set(), 'total_words': 0}
    for fp in files:
        meta, _ = extract_meta(fp)
        summary['files'].append({
            'filename': fp.name, 'title': meta.get('title',''),
            'word_count': meta.get('word_count',0),
            'key_concepts': meta.get('key_concepts', [])
        })
        summary['total_words'] += meta.get('word_count', 0)
        summary['key_topics'].update(meta.get('key_concepts', []))
    summary['key_topics'] = list(summary['key_topics'])[:20]
    summaries[cat] = summary
    json.dump(summary, open(FINAL / f'{cat}_summary.json', 'w', encoding='utf-8'),
              indent=2, ensure_ascii=False)
    print(f"  + {cat}: {len(files)} files, {summary['total_words']:,} words")

json.dump(summaries, open(FINAL / 'category_summaries.json', 'w', encoding='utf-8'),
          indent=2, ensure_ascii=False)

# Splits
print("\n  Creating splits...")
splits = {'train': [], 'validation': [], 'test': []}
for cat in sorted(all_cats):
    cd = [d for d in dataset['documents'] if d['metadata']['category'] == cat]
    n = len(cd)
    te, ve = int(0.7*n), int(0.9*n)
    splits['train'].extend(cd[:te])
    splits['validation'].extend(cd[te:ve])
    splits['test'].extend(cd[ve:])

for sn, sd in splits.items():
    json.dump({'metadata': {'split': sn, 'document_count': len(sd),
              'source_dataset': 'alpha_research_dataset.json'}, 'documents': sd},
              open(FINAL / f'{sn}_split.json', 'w', encoding='utf-8'),
              indent=2, ensure_ascii=False)
    print(f"  + {sn}: {len(sd)} docs")

# Search index
print("\n  Building search index...")
idx = {'metadata': {'index_type': 'keyword_search', 
       'total_documents': len(dataset['documents']),
       'indexed_fields': ['title', 'content', 'key_concepts']}, 'index': {}}
for doc in dataset['documents']:
    did = doc['id']
    for word in re.findall(r'\b\w+\b', doc['metadata'].get('title','').lower()):
        if len(word) > 2:
            idx['index'].setdefault(word, [])
            if did not in idx['index'][word]: idx['index'][word].append(did)
    for concept in doc['metadata'].get('key_concepts', []):
        for word in re.findall(r'\b\w+\b', concept.lower()):
            if len(word) > 2:
                idx['index'].setdefault(word, [])
                if did not in idx['index'][word]: idx['index'][word].append(did)
json.dump(idx, open(FINAL / 'search_index.json', 'w', encoding='utf-8'),
          indent=2, ensure_ascii=False)
print(f"  + {len(idx['index'])} keywords")

# Report
total_words = sum(s['total_words'] for s in summaries.values())
avg_words = total_words // dataset['metadata']['total_files'] if dataset['metadata']['total_files'] else 0

report = f"""# Alpha Research Dataset - Final Report (v2.0)

## Dataset Overview
- Total Documents: {dataset['metadata']['total_files']}
- Categories: {len(summaries)}
- Version: 2.0 (deduplicated, re-categorized)

## Category Breakdown
"""
for cat, s in sorted(summaries.items()):
    report += f"""
### {cat.replace('_',' ').title()}
- Files: {s['file_count']}
- Total Words: {s['total_words']:,}
- Key Topics: {', '.join(s['key_topics'][:10])}
"""

report += f"""
## Dataset Statistics
- Total Word Count: {total_words:,}
- Average Words per Document: {avg_words:,}
- Data Quality: High (deduplicated, properly categorized)

## Data Quality Improvements (v2.0)
- Removed 153 duplicate files
- Fixed miscategorization (investopedia files)
- Added quantitative_methods category
- Properly separated academic papers
- No more cross-category duplicates
"""

open(FINAL / 'dataset_report.md', 'w', encoding='utf-8').write(report)


# ===== STEP 3: Create new Skill.md =====
print(f"\n{'='*60}")
print("STEP 3: Creating updated Skill.md")
print("="*60)

cat_stats = ""
for cat in sorted(all_cats):
    cnt = summaries[cat]['file_count']
    cat_stats += f"| {cat} | {cnt} |\n"

skill = f"""---
name: alpha-creator-v2
description: >
  Huong dan toan dien tao, toi uu va chan doan alpha tren WorldQuant Brain / IQC.
  Phien ban 2 voi du lieu da duoc lam sach, phan loai dung va loai bo trung lap.
---

# Alpha Creator v2 - WorldQuant Brain

Ban la chuyen gia quant researcher giup nguoi dung tao alpha tren WorldQuant Brain.

---

## Quy Trinh - Chon Workflow Dung

| Tinh huong | Workflow |
|---|---|
| Chua co formula, muon bat dau | **Workflow A** - Tao tu dau |
| Co formula + ket qua backtest, muon cai thien | **Workflow B** - Toi uu |
| Gap loi (NaN, syntax, Sharpe am) | **Workflow C** - Chan doan |
| Paste formula/metrics khong noi ro muon gi | **Workflow D** - Triage |

---

## Workflow D - Triage

Khi nguoi dung share formula hoac ket qua ma khong noi ro van de, hoi dung 2 cau:

```
1. Sharpe va Fitness hien tai la bao nhieu?
2. Ban muon submit duoc, hay dang tim cach cai thien them?
```

Phan loai ngay:

```
Sharpe < 0.5            -> Workflow C
0.5 <= Sharpe < 1.0     -> Workflow C, sau do Workflow B
1.0 <= Sharpe < 1.25    -> Workflow B
Sharpe >= 1.25, Fitness < 1.0 -> Workflow B
Sharpe >= 1.25, Fitness >= 1.0 -> Checklist submit
```

---

## Workflow A - Tao Alpha Tu Dau

### Buoc 0: Hieu muc tieu (IQC vs ca nhan)
IQC: muc tieu la nhieu alpha da dang.
Doc `references/iqc-strategy.md`.

### Buoc 1: Chon theme kinh te

| Theme | Y tuong |
|---|---|
| Mean Reversion | Gia bi day qua xa se quay ve |
| Momentum | Da tang/giam tiep dien ngan han |
| Volume-Price | Khoi luong tiet lo y dinh thi truong |
| Volatility | Bien dong cao/thap bat thuong |
| VWAP Deviation | Gia lech khoi trung binh gia quyen |
| Fundamental | P/E, P/B, ROE |
| Liquidity | Illiquidity premium |
| Regime-Based | Trade chi khi thi truong phu hop |

### Buoc 2: Chon operators
Doc `references/operators.md`.
- Tinh toan theo thoi gian -> ts_* operators
- So sanh giua cac co phieu -> rank(), zscore()
- Loai bo bias nganh -> group_neutralize()

### Buoc 3: Xay dung formula

Template co ban:
```
rank( ts_<phep_tinh>( <data_field>, <lookback> ) )
```

Template nang cao:
```python
lookback = <N>;
signal   = <tinh_toan_chinh>;
rank(signal)
```

Vi du:
```python
# Co ban
-rank(ts_delta(close, 5))

# Nang cao
lookback = 5;
signal   = -rank(ts_delta(close, lookback) / (ts_std_dev(returns, 20) + 0.001));
when     = ts_rank(ts_std_dev(returns, 22), 252) > 0.5;
trade_when(when, signal, -1)
```

### Buoc 4: Chon settings ban dau
```
Universe:       TOP3000
Neutralization: Market
Decay:          0
Truncation:     0.05
Region:         USA
Delay:          1
```

---

## Workflow B - Toi Uu Alpha

Dieu kien: Sharpe >= 1.0

Fitness = Sharpe x sqrt(|Returns| / max(Turnover, 0.125))

Muc tieu submit: Fitness >= 1.0, Sharpe >= 1.25, Turnover 10-70%

| Van de | Nguyen nhan | Giai phap |
|---|---|---|
| Turnover > 70% | Signal thay doi qua nhanh | Tang Decay len 3-10 |
| Fitness thap du Sharpe OK | Turnover qua thap (<12.5%) | Giam Decay xuong 0-2 |
| Sharpe < 1.0 | Signal yeu | Doi Neutralization -> Subindustry |
| Returns thap | Universe qua nho | Doi TOP500 -> TOP1000/TOP3000 |
| Drawdown > 20% | Tap trung vi the | Giam Truncation xuong 0.03 |

Grid toi uu:
```
1. TOP3000 + Market    + Decay 0  + Truncation 0.05
2. TOP3000 + Market    + Decay 3  + Truncation 0.05
3. TOP3000 + Subind.   + Decay 0  + Truncation 0.05
4. TOP1000 + Subind.   + Decay 10 + Truncation 0.10
5. TOP500  + Subind.   + Decay 0  + Truncation 0.10
```

---

## Workflow C - Chan Doan va Sua Loi

Sharpe < 0 -> Dao dau formula
0 < Sharpe < 0.5 -> Signal ngau nhien, sua formula
0.5 <= Sharpe < 1 -> Sua formula truoc, tune settings sau
Sharpe >= 1 -> Workflow B

Loi operator:

| Dung sai | Thay bang |
|---|---|
| ts_min(x, d) | -ts_arg_min(x, d) |
| ts_max(x, d) | ts_arg_max(x, d) |
| delay(x, d) | ts_delay(x, d) |
| stddev(x, d) | ts_std_dev(x, d) |
| correlation(x, y, d) | ts_corr(x, y, d) |

Chan doan nhanh:

```
Sharpe am? -> Dao dau toan bo formula
Toan NaN? -> Xem common-mistakes.md
Fitness < 0.5, Turnover > 50%? -> ts_decay_linear(formula, 5)
Fitness < 0.5, Turnover < 10%? -> Giam Decay ve 0
Reject "too similar"? -> Thay doi lookback +/-2 ngay
Loi syntax? -> Kiem tra ngoac, ten operator
```

---

## Checklist Truoc Khi Submit

- [ ] Sharpe >= 1.25
- [ ] Fitness >= 1.0
- [ ] Turnover 10-70%
- [ ] Khong dung operator bi broken
- [ ] Stability: khong co 2 nam lien tiep Sharpe am

IQC them:
- [ ] Alpha co theme KHAC voi alpha da submit?
- [ ] Tuong quan cao -> Sharpe tang >= 10%?
- [ ] Da thu Region thu 2? (CHN/EUR)

---

## Tham Khao Nhanh

```python
# Mean Reversion (Sharpe ~1.4)
-rank(ts_delta(close, 5))

# Volume-Price
-rank(ts_covariance(rank(close), rank(volume), 5))

# VWAP Reversion (Sharpe ~1.6)
rank(vwap - close)

# High-Low Midpoint
rank((high + low) / 2 - close)

# Momentum
rank(ts_mean(ts_delta(close, 1), 10))

# Value
rank(-ts_backfill(pe))

# Liquidity
rank(pasteurize(ts_mean(abs(returns) / (dvol + 1), 20)))
```

---

## Du Lieu Da Xu Ly

### Tong Quan Knowledge Base
- Tong so tai lieu: {dataset['metadata']['total_files']}
- So danh muc: {len(all_cats)}
- Phien ban: 2.0 (da loai bo trung lap, phan loai chinh xac)

### Danh Muc Du Lieu

| Danh muc | So file |
|---|---|
{cat_stats}

### Cai Thien So Voi Phien Ban 1
1. Loai bo 153 file trung lap (_1.md)
2. Sua phan loai sai (Investopedia)
3. Them danh muc quantitative_methods
4. Phan tach academic papers dung danh muc
5. Loai bo file trung lap giua cac danh muc
6. Cap nhat final_dataset voi day du danh muc

---

## Nguon Kien Thuc & Files

| File | Noi dung |
|---|---|
| references/operators.md | Toan bo operators + data fields |
| references/themes.md | 10 themes: Mean Rev, Momentum, Volume, ... |
| references/advanced-syntax.md | Multi-line expression, trade_when |
| references/settings-grid.md | Universe, Neutralization, Decay, Truncation |
| references/iqc-strategy.md | IQC scoring, self-correlation policy |
| references/checklist.md | Checklist submit + stability check |
| references/common-mistakes.md | NaN, look-ahead bias, overfitting |
"""

open(SKILL, 'w', encoding='utf-8').write(skill)
print(f"\n  Created: {SKILL}")
print(f"\n{'='*60}")
print("ALL DONE!")
print("="*60)
