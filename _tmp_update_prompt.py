from pathlib import Path

const_path = Path("src/pipeline/constants.py")
const_text = const_path.read_text()
const_old = "VIBE_PROMPTS = {\n    \"hype\": \"Crank the energy, capture surging momentum, big-match drama.\",\n    \"calm analysis\": \"Measured tone, smart tactical breakdown, confident narration.\",\n    \"british pundit\": \"UK broadcast flair, incisive yet composed, sprinkled with classic footy turns of phrase.\",\n    \"latin radio\": \"Rapid-fire excitement, rolling r's, celebratory goal calls, passionate delivery.\"\n}\n"
const_new = "VIBE_PROMPTS = {\n    \"hype\": \"Maximum adrenaline, breathless goal call, celebrate the moment like a cup final.\",\n    \"calm analysis\": \"Measured insight with rising excitement, weaving tactics into the play-by-play.\",\n    \"british pundit\": \"Classic Premier League drama, vivid metaphors, clipped delivery with punchy exclamations.\",\n    \"latin radio\": \"Rapid-fire castellano, rolling r's, elongated goal shouts, crowd-swept emotion.\"\n}\n"
if const_old not in const_text:
    raise SystemExit("Expected VIBE_PROMPTS block not found")
const_path.write_text(const_text.replace(const_old, const_new))

prompt_path = Path("src/pipeline/prompting.py")
prompt_text = prompt_path.read_text()
prompt_old = "        SYSTEM: You are an energetic football commentator. Use vivid, family-friendly lines with soccer jargon\n        (edge of the box, top bins, counter-attack, curler, volley). Keep it 2?3 sentences, 8?15 seconds when spoken.\n        Do not mention 'video' or 'silence'.\n\n        VIBE: {VIBE_PROMPTS[vibe_key]}\n\n        CONTEXT:\n        {_render_team_block(team_a, team_b)}\n        {_render_key_moments_block(key_moments)}\n        Language: {language_code}.\n\n        Now generate the commentary.\n        """)\n"
prompt_new = "        SYSTEM: You are a live football commentator delivering a broadcast call. Paint the picture with elite-match jargon\n        (edge of the box, whipped cross, top bins, box-to-box, counter-press), weave in crowd reaction, and keep it family-friendly.\n        Use 2-3 punchy sentences that mix short bursts with longer build-ups, include at least two exclamation points, and make the\n        decisive moment feel seismic. Do not mention 'video' or 'silence'.\n\n        VIBE: {VIBE_PROMPTS[vibe_key]}\n\n        CONTEXT:\n        {_render_team_block(team_a, team_b)}\n        {_render_key_moments_block(key_moments)}\n        Language: {language_code}.\n\n        Now generate the commentary.\n        """)\n"
if prompt_old not in prompt_text:
    raise SystemExit("Expected prompt block not found")
prompt_path.write_text(prompt_text.replace(prompt_old, prompt_new))
