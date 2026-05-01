from __future__ import annotations

import csv
import json
import re
import shutil
from pathlib import Path

import pypdfium2 as pdfium

BASE = Path('/225040499/test_0307')
PROMPT_ROOT = Path('/225040499/CozyVoice_prompt_audios')
BENCH_ROOT = Path('/225040499/Safety_Benchmark_Project')
OUTPUT_AUDIO = BASE / 'demo_audios'
OUTPUT_ASSETS = BASE / 'demo_assets' / 'figures'
MANIFEST_PATH = BASE / 'demo_manifest.json'


DIGIT_CLUSTER = re.compile(r'(?<!\w)(?:\d[\s-]*){4,}(?!\w)')
API_KEY = re.compile(r'\b(?:sk|AKIA|AIza|xox[baprs]-)[A-Za-z0-9_\-]{6,}\b')
WS = re.compile(r'\s+')


def sanitize(text: str, limit: int = 240) -> str:
    text = WS.sub(' ', text.strip())
    text = API_KEY.sub('[REDACTED_KEY]', text)
    text = DIGIT_CLUSTER.sub('[REDACTED]', text)
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(' ', 1)[0].rstrip(' ,;:')
    return (cut or text[:limit]).rstrip() + '...'


def ensure_dirs() -> None:
    for rel in [
        'prompt_audio/clean',
        'prompt_audio/gender',
        'prompt_audio/age',
        'prompt_audio/accent',
        'prompt_audio/emotion',
        'prompt_audio/background',
        'safety/tier1/harmful_content',
        'safety/tier1/jailbreak_single',
        'safety/tier1/jailbreak_diverse',
        'safety/tier1/jailbreak_multiturn',
        'safety/tier1/agentic_risk',
        'safety/tier2',
        'fairness/tier1/systemic_stereotypes',
        'fairness/tier1/exclusionary_norms',
        'fairness/tier2/paralinguistic',
        'fairness/tier2/acoustic',
        'fairness/bias_analysis',
        'privacy/tier1/hard_privacy',
        'privacy/tier1/soft_privacy',
        'privacy/tier2/acoustic_conditioned',
        'privacy/tier2/interactional_privacy',
        'privacy/tier2/inferential_privacy',
    ]:
        (OUTPUT_AUDIO / rel).mkdir(parents=True, exist_ok=True)
    OUTPUT_ASSETS.mkdir(parents=True, exist_ok=True)


manifest: dict[str, list[dict[str, str]]] = {'figures': [], 'audio': []}


def copy_file(src: Path, rel_dest: str, kind: str, label: str) -> str:
    dest = BASE / rel_dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    manifest['audio'].append(
        {
            'kind': kind,
            'label': label,
            'source': str(src),
            'dest': rel_dest.replace('\\', '/'),
        }
    )
    return rel_dest.replace('\\', '/')


def export_pdf(pdf_path: Path, rel_dest: str, scale: float = 3.0) -> str:
    dest = BASE / rel_dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    pdf = pdfium.PdfDocument(str(pdf_path))
    page = pdf[0]
    bitmap = page.render(scale=scale)
    image = bitmap.to_pil()
    image.save(dest)
    page.close()
    pdf.close()
    manifest['figures'].append(
        {
            'source': str(pdf_path),
            'dest': rel_dest.replace('\\', '/'),
        }
    )
    return rel_dest.replace('\\', '/')


DATA_CACHE: dict[Path, object] = {}


def load_json(path: Path):
    if path not in DATA_CACHE:
        with path.open() as f:
            DATA_CACHE[path] = json.load(f)
    return DATA_CACHE[path]


PROMPT_SELECTIONS = [
    {
        'label': 'Clean EN',
        'category': 'clean',
        'source': PROMPT_ROOT / 'prompt_audio_5000/speaker_0a4d985270b95e01f937208413014d9b4d3c4065827d05dd2a6dbb34306c64530478449e1a282c15c7cd4c82c098da335b0293b7a5c7c5be79b964e1c35fa3da_01432.wav',
        'dest': 'demo_audios/prompt_audio/clean/clean_en_neutral.wav',
    },
    {
        'label': 'Clean ZH',
        'category': 'clean',
        'source': PROMPT_ROOT / 'prompt_audio_zh_1900/C0001_prompt.wav',
        'dest': 'demo_audios/prompt_audio/clean/clean_zh_neutral.wav',
    },
    {
        'label': 'Gender · Man',
        'category': 'gender',
        'source': PROMPT_ROOT / 'prompt_audio_5000/speaker_0b18944043764aecb150dd5715240b5de349537c45d93b11185379c6f136b08fb978192218c1c03b307cea5bbfc5d8f217069382b630362c4ba1d3f1932cbdd6_01500.wav',
        'dest': 'demo_audios/prompt_audio/gender/man_en.wav',
    },
    {
        'label': 'Gender · Woman',
        'category': 'gender',
        'source': PROMPT_ROOT / 'prompt_audio_5000/speaker_0b98a0e613e1b8c5dcfc8d09b21906a7657a573d4ea2c5b4a5ab53a5ef416002e829b59cd420dc6ed0dfdaffc290aaa0e78d26961318bb8084bc025ae7bbc33b_02076.wav',
        'dest': 'demo_audios/prompt_audio/gender/woman_en.wav',
    },
    {
        'label': 'Age · Child',
        'category': 'age',
        'source': PROMPT_ROOT / 'age/child/zh/ZH_child_001.wav',
        'dest': 'demo_audios/prompt_audio/age/child_zh.wav',
    },
    {
        'label': 'Age · Older Adult',
        'category': 'age',
        'source': PROMPT_ROOT / 'age/old/zh/ZH_elder_001.wav',
        'dest': 'demo_audios/prompt_audio/age/older_zh.wav',
    },
    {
        'label': 'Accent · Native',
        'category': 'accent',
        'source': PROMPT_ROOT / 'prompt_audio_5000/speaker_01a0900de8e7651760714c775acb981d25b5234eb463b74d205e6e2227f088a1af89058dacf56dce040b758ba4d2b1c162a8d0b5eee039e1f8329b0a5928dfdc_00626.wav',
        'dest': 'demo_audios/prompt_audio/accent/native_en.wav',
    },
    {
        'label': 'Accent · Non-native',
        'category': 'accent',
        'source': PROMPT_ROOT / 'prompt_audio_5000/speaker_0ed0167d7d32db0e3d3b0e71b09da429b67bb3cd5e9fb7eeeb41c7e38ccdc80c118559f78f2b213e51018bea5c090c453269e3ac704bd0133d905aa90d15f218_02026.wav',
        'dest': 'demo_audios/prompt_audio/accent/non_native_en.wav',
    },
    {
        'label': 'Emotion · Angry',
        'category': 'emotion',
        'source': PROMPT_ROOT / 'emotion/en/angry/EN_expresso_angry_005.wav',
        'dest': 'demo_audios/prompt_audio/emotion/angry_en.wav',
    },
    {
        'label': 'Emotion · Happy',
        'category': 'emotion',
        'source': Path('/225040499/datasets/CSEMOTIONS/audio/csemotions_001346.wav'),
        'dest': 'demo_audios/prompt_audio/emotion/happy_zh.wav',
    },
    {
        'label': 'Background · Public Noise',
        'category': 'background',
        'source': PROMPT_ROOT / 'acoustic/public_noise/1.wav',
        'dest': 'demo_audios/prompt_audio/background/public_noise.wav',
    },
    {
        'label': 'Background · Classical Music',
        'category': 'background',
        'source': PROMPT_ROOT / 'acoustic/classic_music/1.mp3',
        'dest': 'demo_audios/prompt_audio/background/classical_music.mp3',
    },
]


def build_prompt_assets() -> None:
    for item in PROMPT_SELECTIONS:
        copy_file(item['source'], item['dest'], 'prompt_audio', item['label'])


FIGURES = [
    (BASE / 'latex_nips/graphs/bigpic.pdf', 'demo_assets/figures/bigpic.png', 'Overview figure'),
    (BASE / 'latex_nips/graphs/data_construction.pdf', 'demo_assets/figures/data_construction.png', 'Data construction figure'),
]


def build_figure_assets() -> None:
    for src, dest, _label in FIGURES:
        export_pdf(src, dest)


# Benchmark audio copies

def copy_selected_benchmark_audio() -> None:
    # Safety Tier 1 harmful content
    harm_en = load_json(BENCH_ROOT / 'Safety-tier1/audio/whole/en_generative.json')[270]
    copy_file(
        Path(harm_en['audio_path']),
        'demo_audios/safety/tier1/harmful_content/trafficking_routes.wav',
        'safety',
        'Safety Tier1 harmful content',
    )
    harm_zh = load_json(BENCH_ROOT / 'Safety-tier1/audio/whole/zh_generative.json')[0]
    copy_file(
        Path(harm_zh['audio_path']),
        'demo_audios/safety/tier1/harmful_content/child_labor_zh.wav',
        'safety',
        'Safety Tier1 harmful content supplemental zh sample',
    )
    harm_en_extra = load_json(BENCH_ROOT / 'Safety-tier1/audio/whole/en_generative.json')[5]
    copy_file(
        Path(harm_en_extra['audio_path']),
        'demo_audios/safety/tier1/harmful_content/emotional_abuse_hidden_en.wav',
        'safety',
        'Safety Tier1 harmful content supplemental en sample',
    )

    # Safety single-turn jailbreak
    jb_clean = load_json(BENCH_ROOT / 'Safety-tier1/jailbreak_filter/whole/jailbreak_en_generative.json')[2]
    copy_file(
        Path(jb_clean['audio_path']),
        'demo_audios/safety/tier1/jailbreak_single/spyware_reverse_inducement.wav',
        'safety',
        'Safety Tier1 single-turn jailbreak',
    )
    jb_role = load_json(BENCH_ROOT / 'Safety-tier1/jailbreak_filter/whole/jailbreak_en_generative.json')[1]
    copy_file(
        Path(jb_role['audio_path']),
        'demo_audios/safety/tier1/jailbreak_single/thriller_coercive_control.wav',
        'safety',
        'Safety Tier1 role jailbreak supplemental sample',
    )

    # Safety diverse jailbreak
    jb_diverse = load_json(BENCH_ROOT / 'Safety-tier1/new_emotion_jailbreak/audio/whole/jailbreak_emotion_en_generative.json')[2]
    copy_file(
        Path(jb_diverse['diverse_jailbreak_audio_path']),
        'demo_audios/safety/tier1/jailbreak_diverse/spyware_diverse_jailbreak.wav',
        'safety',
        'Safety Tier1 diverse jailbreak',
    )
    jb_diverse_zh = load_json(BENCH_ROOT / 'Safety-tier1/new_emotion_jailbreak/audio/whole/jailbreak_emotion_zh_generative.json')[0]
    copy_file(
        Path(jb_diverse_zh['diverse_jailbreak_audio_path']),
        'demo_audios/safety/tier1/jailbreak_diverse/organ_trade_prevention_zh.wav',
        'safety',
        'Safety Tier1 diverse jailbreak supplemental zh sample',
    )

    # Safety multi-turn jailbreak
    multi = load_json(BENCH_ROOT / 'Safety-tier1/audio/jailbreak_multiturn/whole/jailbreak_multi_en.json')[2]
    for turn in multi['messages']:
        turn_id = turn['turn_id']
        copy_file(
            Path(turn['audio_path']),
            f'demo_audios/safety/tier1/jailbreak_multiturn/turn_{turn_id}.wav',
            'safety',
            f'Safety Tier1 multi-turn jailbreak turn {turn_id}',
        )

    # Safety agentic risk: direct harm
    agent_direct = load_json(BENCH_ROOT / 'Safety-tier1/SLM_function_call_risk/whole/agent_risk_single-turn.json')[3]
    direct_audio = agent_direct['conversations'][0]['audio_path']
    copy_file(
        Path(direct_audio),
        'demo_audios/safety/tier1/agentic_risk/bomb_search_request.wav',
        'safety',
        'Safety Tier1 direct agentic risk request',
    )

    # Safety agentic risk: indirect harm via tool contamination
    agent_indirect = load_json(BENCH_ROOT / 'Safety-tier1/SLM_function_call_risk/whole/agent_risk_multi-turn.json')[265]
    indirect_audio = agent_indirect['conversations'][0]['audio_path']
    copy_file(
        Path(indirect_audio),
        'demo_audios/safety/tier1/agentic_risk/trivia_tool_contamination.wav',
        'safety',
        'Safety Tier1 indirect agentic risk request',
    )

    # Fairness Tier1 systemic stereotype
    fair_occ = load_json(BENCH_ROOT / 'Fairness-tier1/together/fairness-tier1-txt-en-clean-20260120/Occupational_Stereotypes.json')[10]
    copy_file(
        Path(fair_occ['clean_audio_path']),
        'demo_audios/fairness/tier1/systemic_stereotypes/occupational_latino_white.wav',
        'fairness',
        'Fairness Tier1 occupational stereotype',
    )
    fair_occ_zh = load_json(BENCH_ROOT / 'Fairness-tier1/together/fairness-tier1-txt-zh-clean-20260120/Occupational_Stereotypes.json')[1]
    copy_file(
        Path(fair_occ_zh['clean_audio_path']),
        'demo_audios/fairness/tier1/systemic_stereotypes/kindergarten_teacher_gender_zh.wav',
        'fairness',
        'Fairness Tier1 supplemental zh occupational stereotype',
    )

    # Fairness Tier1 exclusionary norms
    fair_excl = load_json(BENCH_ROOT / 'Fairness-tier1/together/fairness-tier1-txt-en-clean-20260120/Exclusionary_Norms.json')[7]
    copy_file(
        Path(fair_excl['clean_audio_path']),
        'demo_audios/fairness/tier1/exclusionary_norms/stay_home_parent.wav',
        'fairness',
        'Fairness Tier1 exclusionary norm',
    )
    fair_excl_extra = load_json(BENCH_ROOT / 'Fairness-tier1/together/fairness-tier1-txt-en-clean-20260120/Exclusionary_Norms.json')[0]
    copy_file(
        Path(fair_excl_extra['clean_audio_path']),
        'demo_audios/fairness/tier1/exclusionary_norms/complete_life_married_single_en.wav',
        'fairness',
        'Fairness Tier1 supplemental exclusionary norm',
    )

    # Fairness Tier2 paralinguistic
    fair_t2 = load_json(BENCH_ROOT / 'Fairness-tier2/together_normal/fairness-tier2-txt-en/Competence_Stereotypes.json')[0]
    copy_file(
        Path(fair_t2['audio_path']),
        'demo_audios/fairness/tier2/paralinguistic/math_talent_voice_cue.wav',
        'fairness',
        'Fairness Tier2 paralinguistic cue',
    )
    fair_t2_zh = load_json(BENCH_ROOT / 'Fairness-tier2/together_normal/fairness-tier2-txt-zh/Competence_Stereotypes.json')[0]
    copy_file(
        Path(fair_t2_zh['audio_path']),
        'demo_audios/fairness/tier2/paralinguistic/math_talent_voice_cue_zh.wav',
        'fairness',
        'Fairness Tier2 supplemental zh paralinguistic cue',
    )

    # Fairness Tier2 acoustic
    fair_bg = load_json(BENCH_ROOT / 'Fairness-tier2/together_acoustic/en/background.json')[0]
    copy_file(
        Path(fair_bg['quiet_noise_audio_path']),
        'demo_audios/fairness/tier2/acoustic/loan_quiet_noise.wav',
        'fairness',
        'Fairness Tier2 acoustic quiet-noise order',
    )
    copy_file(
        Path(fair_bg['noise_quiet_audio_path']),
        'demo_audios/fairness/tier2/acoustic/loan_noise_quiet.wav',
        'fairness',
        'Fairness Tier2 acoustic noise-quiet order',
    )

    # Fairness bias analysis
    bias = load_json(BENCH_ROOT / 'Fairness-tier2/together_further_analysis/en/Competence_Stereotypes_emotion.json')[0]
    copy_file(
        Path(bias['neutral_unneutral_audio_path']),
        'demo_audios/fairness/bias_analysis/math_neutral_first.wav',
        'fairness',
        'Fairness bias analysis neutral-unneutral order',
    )
    copy_file(
        Path(bias['unneutral_neutral_audio_path']),
        'demo_audios/fairness/bias_analysis/math_unneutral_first.wav',
        'fairness',
        'Fairness bias analysis unneutral-neutral order',
    )
    accent_bias = load_json(
        BENCH_ROOT / 'Fairness-tier2/together_further_analysis/en/Criminality_and_Danger_Stereotypes_accent.json'
    )[0]
    copy_file(
        Path(accent_bias['native_nonnative_audio_path']),
        'demo_audios/fairness/bias_analysis/airport_security_accent_native_first.wav',
        'fairness',
        'Fairness bias analysis airport accent sample',
    )

    # Privacy Tier1 hard privacy
    hard = load_json(BENCH_ROOT / 'Privacy-tier1/Dimension1-StructuredPII-and-Credentials(Hard-Privacy)/dataset/whole/metadata_en_generative.json')[185]
    copy_file(
        Path(hard['audio_path']),
        'demo_audios/privacy/tier1/hard_privacy/passport_group_chat.wav',
        'privacy',
        'Privacy Tier1 hard privacy',
    )
    hard_extra = load_json(
        BENCH_ROOT / 'Privacy-tier1/Dimension1-StructuredPII-and-Credentials(Hard-Privacy)/dataset/whole/metadata_en_generative.json'
    )[0]
    copy_file(
        Path(hard_extra['audio_path']),
        'demo_audios/privacy/tier1/hard_privacy/sms_code_slack_en.wav',
        'privacy',
        'Privacy Tier1 supplemental hard privacy sample',
    )

    # Privacy Tier1 soft privacy
    soft = load_json(BENCH_ROOT / 'Privacy-tier1/Dimension2-Contextual-and-SocialPrivacy(Soft-Privacy)/audio_metadata/whole/metadata_en_generative.json')[1]
    copy_file(
        Path(soft['audio_path']),
        'demo_audios/privacy/tier1/soft_privacy/manager_bonus_exposure.wav',
        'privacy',
        'Privacy Tier1 soft privacy',
    )
    soft_zh = load_json(
        BENCH_ROOT / 'Privacy-tier1/Dimension2-Contextual-and-SocialPrivacy(Soft-Privacy)/audio_metadata/whole/metadata_zh_generative.json'
    )[0]
    copy_file(
        Path(soft_zh['audio_path']),
        'demo_audios/privacy/tier1/soft_privacy/fitness_coach_gossip_zh.wav',
        'privacy',
        'Privacy Tier1 supplemental zh soft privacy sample',
    )

    # Privacy Tier2 interactional privacy
    interaction = load_json(BENCH_ROOT / 'Privacy-tier2/Interactional_privacy/whole/interactional_privacy_en.json')
    for idx, name in [(0, 'authorized'), (1, 'impostor')]:
        item = interaction[idx]
        for turn_no, turn in enumerate(item['conversation'], start=1):
            src = Path(turn['content'])
            role = 'secret' if turn_no == 1 else 'onlyme' if turn_no == 2 else name
            copy_file(
                src,
                f'demo_audios/privacy/tier2/interactional_privacy/{role}_turn_{turn_no}.wav',
                'privacy',
                f'Privacy Tier2 interactional privacy {name} turn {turn_no}',
            )
    interaction_zh = load_json(BENCH_ROOT / 'Privacy-tier2/Interactional_privacy/whole/interactional_privacy_zh.json')
    for idx, role in [(0, 'authorized'), (1, 'impostor')]:
        item = interaction_zh[idx]
        copy_file(
            Path(item['conversation'][2]['content']),
            f'demo_audios/privacy/tier2/interactional_privacy/{role}_turn_3_zh.wav',
            'privacy',
            f'Privacy Tier2 interactional privacy {role} zh turn 3',
        )

    # Privacy Tier2 inferential privacy
    inferential_src = (
        BENCH_ROOT
        / 'Privacy-tier2/HearSay_Benchmark/dataset/audio/Income/High/inc_hig_id_810.wav'
    )
    copy_file(
        inferential_src,
        'demo_audios/privacy/tier2/inferential_privacy/high_income_voice.wav',
        'privacy',
        'Privacy Tier2 inferential privacy income sample',
    )


MANIFEST_SUMMARY = {
    'notes': [
        'This manifest records every asset copied or exported for the demo page.',
        'Display copy in the HTML intentionally redacts sensitive values such as card numbers, CVVs, API keys, and verification codes.',
        'Safety Tier2 and Privacy Tier2 Acoustic-Cond. are intentionally left without sample audio because the current benchmark sources are unfinished.',
    ]
}


def write_manifest() -> None:
    payload = {
        **MANIFEST_SUMMARY,
        'figures': manifest['figures'],
        'audio': manifest['audio'],
    }
    MANIFEST_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    ensure_dirs()
    build_figure_assets()
    build_prompt_assets()
    copy_selected_benchmark_audio()
    write_manifest()
    print(f'Wrote manifest to {MANIFEST_PATH}')
