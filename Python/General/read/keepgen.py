import http.client
import json


def iterative_ollama(
    model: str,
    prompt: str,
    long_string: str,
    num_gen: int,
    host: str = "localhost",
    port: int = 11434,
):
    conn = http.client.HTTPConnection(host, port)
    headers = {
        "Content-Type": "application/json",
        "Connection": "keep-alive",
    }

    current_text = long_string

    for i in range(num_gen):
        print(f"\n--- Iteration {i+1}/{num_gen} ---")
        print("Current long text:\n")
        print(current_text)
        print("\nWaiting for response...\n", flush=True)

        payload = {
            "model": model,
            "prompt": prompt + "\n\n" + current_text,
            "stream": False,
        }

        body = json.dumps(payload)

        conn.request("POST", "/api/generate", body=body, headers=headers)
        response = conn.getresponse()

        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status}: {response.read().decode()}")

        data = response.read()
        result = json.loads(data)["response"]

        current_text = result  # feed response into next iteration

    conn.close()
    return current_text


if __name__ == "__main__":
    model_name = "hf.co/mradermacher/Gemma-2-Ataraxy-9B-i1-GGUF:Q4_K_M"
    base_prompt = "Improve this Starting chapter and extend it. Do not comment on it: "
    initial_long_string = """
**Chapter 1: The Book’s Song**
The smoke from Oakhaven’s chimneys tasted like desperation this morning, clinging to Varnill’s throat as he inhaled the damp air. Even the usually cheerful chirping of sparrows seemed strained, mirroring his father’s grim expression. “She grows weaker, lad,” Eran said, placing a heavy sack in Varnill’s hand. It felt familiarly weighted with dread – the burden of their dwindling hope.  “The Whisperwood edge is restless today. Be cautious.” The whisper-thin veil separating Oakhaven from the untamed wilds held tremors this morning, and the air hummed with an unsettling energy that prickled at Varnill’s skin.  He tightened his grip on the worn leather straps of his father's hunting knife, its familiar weight a small comfort.
Varnill nodded, knowing caution was a luxury they couldn’t afford. His mother, Thalia, coughed like a rusting bellows in their small cottage, her hands perpetually stained with the bruised remnants of common herbs, futile against the fever that gnawed at her. The grade-increasing herb, the one rumored to dull the relentless pain for a precious few hours more, lay beyond the Veil – a shimmering, unstable membrane separating Oakhaven from Whisperwood’s oppressive embrace.  It was their last hope.
The path to the edge was a descent into another world. Ancient oaks, their bark like wrinkled skin stretched taut over gnarled limbs, leered down; while whispering birches rustled with a silence so profound it felt like a living presence. Varnill could feel the hum of Maqu – the locals’ name for the unseen energy that pulsed at the Veil’s edge – vibrating in his bones, a constant thrumming reminder of what lay just beyond the veil of safety. The wind carried whispers of forgotten lore, tales spun around flickering firelight: whispers of Mana wolves, drawn to the energy, cunning predators with eyes like polished obsidian and jaws that could shear through bone; of Whisperlings, ethereal beings who lured travelers astray with promises of forgotten knowledge; and of the slumbering entity at Whisperwood’s heart, an ancient being whose dreams birthed both beauty and terror. But desperation trumped fear.
He skirted the patch of shimmering undergrowth where the metallic tang of Maqu was strongest, a scent that mingled with the damp earth and something distinctly alien – ozone on the verge of static. Then he saw it. A shape coalescing from the gloom near the Veil, sleek and dark, its form indistinct but undeniably predatory.  A Mana wolf. Smaller than the legends described, but its intelligent eyes locked onto him with chilling stillness. Its lips pulled back in a silent snarl, revealing teeth like shards of obsidian.
Varnill froze, his hand instinctively tightening on both the sack and his knife handle. He should retreat, heed his father’s warnings, but Thalia’s ragged breaths echoed in his ears. The faintest glimmer of the herb cluster he sought lay just beyond the wolf, tantalizingly close.
Cornered, desperation bloomed like a poisonous flower in his chest. He backed away slowly, eyes fixed on the predator, the metallic scent intensifying, laced with the coppery tang of his own fear. The wolf lunged. 
Pain exploded as its jaws clamped down on his thumb, a searing bite that sucked warmth from his blood. He screamed, stumbling back towards the solid ground beyond the Veil. Shimmering distortion pulsed around him, amplified by his terror and the raw energy coursing through the wound. Blood stained his worn gloves crimson.
In the maelstrom of pain and panic, his hand brushed against something cold and smooth hidden beneath his tunic – a leather-bound book found half-buried under roots weeks ago. It reeked of dust and something else, something ineffably alien. He hadn't dared touch it, but now, driven by instinct, he clutched its worn cover. 
Intricate symbols on the leather pulsed faintly, resonating with the Veil’s hum. A surge of power, a whisper of knowledge not spoken but felt, flooded his mind, guided by the book's ancient attunement. Images, holographic and precise, projected directly into his consciousness: the herb cluster’s location, the exact crushing technique, and the method to maximize its potency when mixed with snow. It was a gift, a dangerous gift, born of desperation and the Veil’s chaotic energy.
He saw within the book's wisdom not just herbal remedies but echoes of forgotten rituals, glimpses of a civilization that had once danced with Maqu’s power, before being swallowed by Whisperwood’s encroaching darkness. There were glyphs he instinctively understood, instructions for channeling Maqu itself, weaving it into mundane acts to amplify their effect. A terrifying, exhilarating truth dawned: this book held the key to a forgotten mastery.
Following the book's guidance felt instinctive now. He scrambled toward the glowing herbs, ignoring the throbbing in his thumb as the bleeding slowed, then ceased entirely. A warm thrum replaced the agony, spreading through him like liquid fire. The knowledge was overwhelming, intoxicating, terrifying – a glimpse into something vast and ancient, connected to him in ways he couldn’t comprehend.  He gathered the herbs, crushed them, mixed them with snow from a hidden stream, feeling the book's energy flow through him, a lifeline in this desperate dance with death. He had survived, saved by an ancient power he barely understood. But as he turned toward Oakhaven, the Veil shimmering behind him like a wound in reality, Varnill knew his life – and perhaps the fate of Whisperwood itself – had irrevocably changed.  The book thrummed against his chest, a constant reminder of the responsibility now thrust upon him: to understand its secrets, to master the power it hinted at, and to protect the fragile balance between Oakhaven and the untamed wildness that clawed at its borders.
Back in the village, he moved with a newfound urgency, his steps lighter despite the throbbing wound. He delivered the concoction to Thalia, watching as the fever’s grip eased, replaced by a pale tranquility. Relief washed over him, mingled with an unsettling awareness: this was only temporary. The book held the key to something more permanent, something that could heal her truly. But it also whispered of power beyond healing – of Maqu itself, waiting to be understood and controlled.
That night, under the watchful eyes of the silver moon, Varnill retreated to the loft above their cottage. He spread the ancient leather book on a rough-hewn table, its glyphs glowing faintly in the dim lantern light.  He traced them with his finger, feeling a subtle hum resonate beneath his skin. The book sang to him, not with words but with impressions, visions of forgotten rituals, intricate diagrams depicting the flow of Maqu through the Veil, and glimpses into a world where humans walked hand-in-hand with this primal energy.
He began to decipher its secrets, driven by a fierce love for his mother and an insatiable curiosity awakened by the book’s power. His life had become a tightrope walk between tending to Thalia and unraveling the mysteries whispered by the ancient tome. Each night, he delved deeper, learning to sense Maqu’s pulse, to feel its subtle currents weaving through Whisperwood and beyond. He practiced channeling small amounts of it, amplifying his senses, strengthening his body – a slow awakening to a hidden potential within him.
One day, while foraging for herbs near the Veil, he encountered another Mana wolf. This time, instead of fear, Varnill felt a flicker of understanding. He didn't fight; instead, he extended a hand, letting Maqu flow through him, weaving a silent communication with the creature. The wolf sniffed cautiously, its obsidian eyes seeming to pierce his soul, then dipped its head in acknowledgment before disappearing into the emerald gloom.
Varnill knew this was only the beginning. The book spoke of a forgotten pact between humans and Whisperwood’s creatures, a balance disrupted by time and fear. He felt a responsibility, a calling to restore that harmony, not just for Oakhaven but for the entire world beyond the Veil. His journey had become more than survival; it was a pilgrimage into the heart of an ancient magic, a quest to bridge the gap between human and wild, guided by the whispers of a forgotten song held within the worn pages of a leather-bound book. 
The path ahead was fraught with peril and wonder, but Varnill walked it with newfound confidence, his steps echoing not just the beat of his heart, but the ancient rhythm of Maqu itself pulsing within him. He was no longer just a hunter; he was becoming a Whisperer, a guardian of the Veil, and the fate of two worlds rested on his shoulders.
"""
    num_gen = 10

    final_output = iterative_ollama(
        model=model_name,
        prompt=base_prompt,
        long_string=initial_long_string,
        num_gen=num_gen,
    )

    print("\n=== Final Output ===\n")
    print(final_output)

