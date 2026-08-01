import os
import json
import glob
import random
import requests
import shutil
import sys
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
from pathlib import Path
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Import upload functions
try:
    from upload.upload_instagram import upload_to_instagram
    from upload.upload_threads import upload_to_threads
    from upload.upload_facebook import upload_to_facebook, upload_to_facebook_story
    from upload.upload_to_youtube import upload_to_youtube
except ImportError as e:
    print(f"Error importing upload modules: {e}")
    # Still want to proceed or stop?
    pass

PROCESSED_DIR = "Processed_Videos"
PUBLISHED_LOG = "published_videos.json"

def get_already_published():
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def get_repost_counts():
    """Count how many times each video has been posted."""
    published = get_already_published()
    counts = {}
    for entry in published:
        vname = entry.get("video_name", "")
        counts[vname] = counts.get(vname, 0) + 1
    return counts

def mark_as_published(video_name, metadata):
    published = get_already_published()
    published.append({
        "video_name": video_name,
        "metadata": metadata
    })
    with open(PUBLISHED_LOG, 'w', encoding='utf-8') as f:
        json.dump(published, f, indent=4)

def select_video(specific_video=None):
    published = [item["video_name"] for item in get_already_published()]
    all_videos = sorted(glob.glob(os.path.join(PROCESSED_DIR, "*.mp4")))

    if specific_video:
        # specific_video might be a full path or just a filename
        if os.path.exists(specific_video):
            # It's a full path
            vid_path = specific_video
            name = os.path.basename(specific_video)
        else:
            # It's just a filename, join with PROCESSED_DIR
            vid_path = os.path.join(PROCESSED_DIR, specific_video)
            name = specific_video

        if os.path.exists(vid_path):
            if name in published:
                post_count = sum(1 for p in published if p == name)
                print(f"🔄 Video {name} was already published ({post_count}x) - Re-publishing (recycling)")
            return vid_path, name
        else:
            print(f"❌ Error: Specific video {name} not found")
            return None, None

    # Find unpublished videos first
    unpublished = [(vid, os.path.basename(vid)) for vid in all_videos if os.path.basename(vid) not in published]

    if unpublished:
        vid, name = unpublished[0]
        return vid, name

    # All videos published - use weighted random selection (less posted = more likely)
    if all_videos:
        repost_counts = get_repost_counts()
        weights = []
        for vid in all_videos:
            name = os.path.basename(vid)
            count = repost_counts.get(name, 0)
            weight = max(1, 1000 // (3 ** min(count, 6)))
            weights.append(weight)

        selected_vid = random.choices(all_videos, weights=weights, k=1)[0]
        name = os.path.basename(selected_vid)
        post_count = repost_counts.get(name, 0)
        print(f"🎲 All videos published. Weighted random reuse (posted {post_count}x): {name}")
        return selected_vid, name

    return None, None

def generate_caption():
    import random
    import time

    api_key = os.getenv("POLLINATIONS_API_KEY")
    model = os.getenv("AI_MODEL", "openai")

    fallback_titles = [
        "Angelina Jolie's Most Iconic Movie Roles",
        "The Power and Grace of Angelina Jolie",
        "Angelina Jolie — A Hollywood Icon",
        "Best Angelina Jolie Scenes of All Time",
        "From Lara Croft to Maleficent: Angelina Jolie",
        "Angelina Jolie's Journey to Stardom",
        "Top 5 Angelina Jolie Performances",
        "Angelina Jolie Moments That Define Her Career",
        "The Timeless Beauty of Angelina Jolie",
        "Angelina Jolie Through the Years",
        "Why Angelina Jolie Is One of the Greatest Actresses",
        "Behind the Scenes With Angelina Jolie",
        "Angelina Jolie's Most Powerful Performances",
        "Rediscovering Angelina Jolie's Best Films",
        "A Tribute to Angelina Jolie",
    ]

    fallback_descriptions = [
        "From the jungle temples of Lara Croft to the dark magic of Maleficent, Angelina Jolie has commanded the screen for decades. Her presence is magnetic, her performances unforgettable. This tribute celebrates the woman who has captivated audiences around the world. Drop a 🎬 if you love Angelina Jolie! #angelinajolie #laracroft #maleficent #actress #hollywood #movieclips #cinema #icon #fanpage #tribute",
        "Angelina Jolie didn't just become a star — she became a global icon. From her Oscar-winning performances to her humanitarian work, she has inspired millions with her strength, beauty, and compassion. Here's a look at the roles that defined her legendary career. Like if you admire her! ✨ #angelinajolie #hollywood #actress #icon #oscarwinner #cinema #inspiration #tribute #fanpage #movieclips",
        "There are movie stars, and then there's Angelina Jolie. With her intense presence and fearless choices, she has delivered some of cinema's most powerful performances. These are the scenes that showcase her incredible range and magnetism. Comment your favorite Angelina Jolie film below! 🎥 #angelinajolie #movies #actress #bestscenes #cinema #hollywood #icon #tribute #fanpage #film",
        "Angelina Jolie's rise to fame is a story of talent, determination, and reinvention. From indie films to blockbuster franchises, she has done it all — and done it brilliantly. This tribute honors her remarkable journey through Hollywood and beyond. Share this with a fellow fan! 🌟 #angelinajolie #journey #hollywood #actress #inspiration #cinema #icon #tribute #fanpage #film",
        "Whether she's wielding a bow as Lara Croft or casting spells as Maleficent, Angelina Jolie brings an unmatched intensity to every role. Her characters are powerful, complex, and unforgettable. Double tap if Angelina Jolie is one of your favorites! 💛 #angelinajolie #laracroft #maleficent #actress #hollywood #cinema #movieclips #icon #fanpage #tribute",
        "Angelina Jolie's elegance is as legendary as her action scenes. With grace, intelligence, and undeniable presence, she lights up the red carpet and the screen alike. These moments show the woman behind the iconic roles. Which look is your favorite? Comment below! 👗 #angelinajolie #redcarpet #fashion #style #elegance #hollywood #actress #icon #glamour #fanpage",
        "A career filled with unforgettable performances. From Girl, Interrupted to Changeling, Angelina Jolie has given cinema some of its most emotionally powerful moments. Her dedication to her craft is unmatched. Save this for your next movie night! 🍿 #angelinajolie #films #actress #filmography #cinema #hollywood #oscarwinner #girlinterrupted #fanpage #tribute",
        "Behind every iconic performance is a person of remarkable depth. Angelina Jolie's intelligence, warmth, and humanitarian heart shine through in interviews and behind-the-scenes moments. Here's a look at the real woman behind the star. Like if you appreciate her authenticity! 🎥 #angelinajolie #behindthescenes #authentic #interview #hollywood #actress #humanitarian #tribute #fanpage #bts",
        "Angelina Jolie's voice has been used for more than just films — she's a champion for human rights and a voice for those who need it most. Her impact extends far beyond the screen. This tribute honors both the actress and the activist. Share this with someone who admires her! 💬 #angelinajolie #activist #humanitarian #inspiration #hollywood #actress #cinema #tribute #fanpage #legacy",
        "From Oscar-winning dramas to epic action franchises, Angelina Jolie has proven her incredible versatility time and again. Her ability to disappear into any character sets her apart as one of the greatest actresses of our time. Here's to her most powerful performances. Comment your favorite role! 🏆 #angelinajolie #oscarwinner #hollywood #actress #cinema #greatest #filmography #tribute #fanpage #movie",
        "What makes Angelina Jolie extraordinary? Her fearless approach to every role and her unwavering commitment to stories that matter. Whether fierce or vulnerable, she brings authenticity to the screen. This fan tribute celebrates her artistry and impact. Drop a ❤️ if you're a Jolie fan! #angelinajolie #acting #artistry #hollywood #actress #cinema #tribute #fanpage #movieclips #talented",
        "Some actors leave a mark on cinema forever. Angelina Jolie is one of them. Her filmography spans genres and generations, and her legacy continues to inspire new audiences. Here's a celebration of her greatest moments on screen. Like if you agree! 🌟 #angelinajolie #legacy #cinema #hollywood #actress #inspiration #filmography #tribute #fanpage #greatness",
        "There's an undeniable magic in Angelina Jolie's performances. From quiet dramas to sweeping epics, she captivates audiences every single time. This is a celebration of her incredible body of work and the joy she brings to the screen. Double tap for Angelina Jolie! ✨ #angelinajolie #cinema #acting #talent #hollywood #movieclips #actress #tribute #fanpage #film",
        "One actress. Countless unforgettable characters. Angelina Jolie has brought some of cinema's most iconic roles to life, from Lara Croft to Maleficent and beyond. Her legacy is one of power, grace, and compassion. Share this with a fellow Jolie fan! 🦸‍♀️ #angelinajolie #laracroft #maleficent #actress #hollywood #cinema #iconic #tribute #fanpage #film",
        "Angelina Jolie proves that true greatness never fades. Her enduring career is a testament to her talent, her heart, and her unwavering spirit. This fan tribute is our little way of celebrating her impact on film and the world. Like if Angelina Jolie inspires you! 💖 #angelinajolie #hollywood #actress #cinema #legacy #inspiration #icon #tribute #fanpage #film",
    ]

    if not api_key:
        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        print("Warning: POLLINATIONS_API_KEY not found. Using fallback captions.")
        return chosen_title, chosen_desc

    vibes = [
        "admiring and celebratory — speak as a devoted fan paying tribute",
        "cinematic and powerful — make viewers feel the intensity of her performances",
        "warm and appreciative — celebrate her talent, grace and humanitarian heart",
        "inspiring and heartfelt — highlight her journey and impact",
        "nostalgic and fond — celebrate the iconic moments fans love",
        "respectful and admiring — appreciate the craft behind the roles",
        "elegant and glamorous — match the timeless quality of her presence",
    ]
    chosen_vibe = random.choice(vibes)

    prompt = (
        f"Write a completely unique, long, and captivating title and description for a short video "
        f"for the social media page 'AnjoTok Lens'. "
        f"It is a fan page dedicated to the Hollywood actress Angelina Jolie, "
        f"best known for Lara Croft: Tomb Raider, Maleficent, Girl, Interrupted, Mr. & Mrs. Smith, and Changeling. "
        f"It shares appreciation content, iconic movie moments, and tributes to her career and humanitarian work. "
        f"It is an unofficial fan page that does not impersonate anyone - just celebrates her work. "
        f"Make the vibe {chosen_vibe}. "
        f"The description should be LONG (4-6 sentences minimum), deeply engaging, and personal. "
        f"Include engagement calls-to-action such as: "
        f"Like if you love Angelina Jolie! Comment your favorite Angelina Jolie film below! Share this with a fellow movie lover! Follow AnjoTok Lens for daily Angelina Jolie appreciation! "
        f"Include relevant hashtags in ALL LOWERCASE such as #angelinajolie #laracroft #maleficent #actress #hollywood #cinema #oscarwinner #mrandmrssmith #girlinterrupted #movielover #film #fanpage #appreciation #tribute. "
        f"Return ONLY a valid JSON object in this format: {{\"title\": \"<title>\", \"description\": \"<description>\"}} "
        f"Do not include any other text or markdown block backticks."
    )
    url = "https://gen.pollinations.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "seed": random.randint(1, 999999)
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        data = response.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

        content = content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)

        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        return result.get("title", chosen_title), result.get("description", chosen_desc)
    except Exception as e:
        print(f"Error generating caption: {e}")
        return random.choice(fallback_titles), random.choice(fallback_descriptions)

def main():
    print("=" * 60)
    print("🚀 DAILY AUTOMATION STARTING")
    print("=" * 60)
    
    specific_video = sys.argv[1] if len(sys.argv) > 1 else None
    video_path, video_name = select_video(specific_video)
    if not video_path:
        print("✅ No new videos found to publish. Exiting.")
        return
        
    print(f"👉 Selected Video: {video_name}")
    print("🧠 Generating caption via Pollination AI...")
    title, description = generate_caption()
    
    print(f"📝 Title: {title}")
    print(f"📝 Description:\n{description}")
    
    # Combined caption for platforms that use a single text field
    combined_caption = f"{title}\n\n{description}"
    
    success_flags = {
        "instagram_reel": False,
        "instagram_story": False,
        "facebook_reel": False,
        "facebook_story": False,
        "threads": False,
        "youtube": False
    }
    
    # Instagram Reels
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=False)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_reel"] = True
    except Exception as e:
        print(f"❌ Instagram Reel upload failed: {e}")
        
    # Instagram Stories
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=True)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_story"] = True
    except Exception as e:
        print(f"❌ Instagram Story upload failed: {e}")
        
    # Facebook Reels
    try:
        result = upload_to_facebook(video_path, description, title=title)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_reel"] = True
    except Exception as e:
        print(f"❌ Facebook Reel upload failed: {e}")
        
    # Facebook Stories
    try:
        result = upload_to_facebook_story(video_path)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_story"] = True
    except Exception as e:
        print(f"❌ Facebook Story upload failed: {e}")
        
    # Threads
    try:
        result = upload_to_threads(video_path, combined_caption)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Threads: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["threads"] = True
    except Exception as e:
        print(f"❌ Threads upload failed: {e}")
        
    # YouTube Shorts
    try:
        upload_to_youtube(video_path, title, description, tags=["angelinajolie", "laracroft", "maleficent", "actress", "hollywood", "cinema", "oscarwinner", "mrandmrssmith", "girlinterrupted", "movielover", "film", "fanpage", "appreciation", "tribute"])
        success_flags["youtube"] = True
    except Exception as e:
        print(f"❌ YouTube upload failed: {e}")
        
    # Record as published regardless of partial success,
    # to avoid repeating the same video. Alternatively, only record if fully successful.
    print("\n✅ Marking video as published.")
    
    # Check if this is a recycled video (already in published_videos.json)
    published_list = get_already_published()
    is_recycled = any(item["video_name"] == video_name for item in published_list)
    
    if is_recycled:
        print(f"   🔄 This is a recycled video (re-publishing)")
    
    mark_as_published(video_name, {
        "title": title,
        "description": description,
        "success_flags": success_flags,
        "recycled": is_recycled
    })
    
    # Move the published video to Published_Videos folder
    published_dir = "Published_Videos"
    if not os.path.exists(published_dir):
        os.makedirs(published_dir)
        
    try:
        dest_path = os.path.join(published_dir, video_name)
        shutil.move(video_path, dest_path)
        print(f"📦 Moved published video to {dest_path}")
    except Exception as e:
        print(f"❌ Failed to move published video: {e}")
    
    print("🎉 DAILY AUTOMATION COMPLETE")

if __name__ == "__main__":
    main()
