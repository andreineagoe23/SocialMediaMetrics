import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import requests

# Set up the scope and authorize the Google Sheets API
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)
sheet = client.open("BrixtonRadio").sheet1

ACCESS_TOKEN = 'n52lJDs9bLjPj5dWGe0LR1IufwukcZ3d'
USER_ID = 'brixtonradiolive'

YOUTUBE_API_KEY = 'AIzaSyAwVM-HcfQx5QPp6emEGQZ4EuBpUaN6fSk'
CHANNEL_ID = 'UCAvtGQclGUkI14zeGw4_FpQ'

# Fetch YouTube data
def get_youtube_data():
    url = f"https://www.googleapis.com/youtube/v3/channels?part=statistics&id={CHANNEL_ID}&key={YOUTUBE_API_KEY}"
    response = requests.get(url)
    data = response.json()
    print(f"YouTube API response: {data}")
    if "items" in data and len(data["items"]) > 0:
        stats = data["items"][0]["statistics"]
        subscriber_count = int(stats["subscriberCount"])

        # Fetch the latest 15 videos
        videos_url = f"https://www.googleapis.com/youtube/v3/search?key={YOUTUBE_API_KEY}&channelId={CHANNEL_ID}&part=id,snippet&order=date&maxResults=15"
        videos_response = requests.get(videos_url)
        videos_data = videos_response.json()

        total_views = 0
        total_likes = 0
        total_comments = 0

        video_details = []

        # Loop through videos to get statistics
        if "items" in videos_data:
            for video in videos_data["items"]:
                video_id = video["id"].get("videoId")
                if video_id:
                    # Get video statistics
                    video_stats_url = f"https://www.googleapis.com/youtube/v3/videos?key={YOUTUBE_API_KEY}&part=statistics,snippet&id={video_id}"
                    video_stats_response = requests.get(video_stats_url)
                    video_stats = video_stats_response.json()

                    if "items" in video_stats and len(video_stats["items"]) > 0:
                        video_statistics = video_stats["items"][0]["statistics"]
                        video_snippet = video_stats["items"][0]["snippet"]
                        video_title = video_snippet["title"]
                        video_publish_date = video_snippet["publishedAt"].split("T")[0]
                        
                        # Extract counts with default to 0 if unavailable
                        video_views = int(video_statistics.get("viewCount", 0))
                        video_likes = int(video_statistics.get("likeCount", 0))
                        video_comments = int(video_statistics.get("commentCount", 0))
                        video_tags = video_snippet.get("tags", [])

                        # Aggregate statistics
                        total_views += video_views
                        total_likes += video_likes
                        total_comments += video_comments

                        # Append video details without description
                        video_details.append([
                            video_publish_date,
                            "YouTube",
                            video_title,
                            video_views,
                            video_likes,
                            video_comments,
                            ", ".join(video_tags)
                        ])

        return subscriber_count, total_views, total_likes, total_comments, video_details
    else:
        print("Error fetching data: ", data)
        return None, None, None, None, None

# Get Mixcloud data
def get_mixcloud_data():
    url = f'https://api.mixcloud.com/{USER_ID}/?metadata=1&access_token={ACCESS_TOKEN}'
    response = requests.get(url)
    print(f"Mixcloud API response: {response.json()}")
    if response.status_code == 200:
        data = response.json()
        mixcloud_data = []

        # Extract relevant profile data
        follower_count = data['follower_count']
        following_count = data['following_count']
        cloudcast_count = data['cloudcast_count']
        favorite_count = data['favorite_count']
        listen_count = data['listen_count']
        
        # Add this summary data to mixcloud_data
        mixcloud_data.append([
            datetime.now().strftime("%Y-%m-%d"),
            "Mixcloud Profile Summary",
            follower_count,
            following_count,
            cloudcast_count,
            favorite_count,
            listen_count
        ])
        
        # Fetch cloudcasts
        cloudcasts_url = data['metadata']['connections']['cloudcasts']
        cloudcasts_response = requests.get(cloudcasts_url)
        
        if cloudcasts_response.status_code == 200:
            cloudcasts = cloudcasts_response.json()['data']
            for cloudcast in cloudcasts:
                title = cloudcast['name']
                plays = cloudcast.get('playback_count', 0)
                likes = cloudcast.get('likes', 0)
                comments = cloudcast.get('comments', 0)
                date = cloudcast['created_time']

                mixcloud_data.append([
                    date.split("T")[0], 
                    "Mixcloud", 
                    title, 
                    plays, 
                    likes, 
                    comments
                ])
        else:
            print("Error fetching cloudcasts:", cloudcasts_response.status_code, cloudcasts_response.text)

        return mixcloud_data
    else:
        print("Error fetching Mixcloud profile data:", response.status_code, response.text)
        return []

# Update Google Sheets with YouTube data
def update_google_sheets():
    subscribers, total_views, total_likes, total_comments, video_details = get_youtube_data()
    mixcloud_data = get_mixcloud_data()

    # Write summary data to Google Sheets
    print("Adding YouTube summary data to Google Sheets...")
    sheet.append_row(["Date", "Platform", "Subscribers", "Total Views", "Total Likes", "Total Comments"])
    sheet.append_row([datetime.now().strftime("%Y-%m-%d"), "YouTube", subscribers, total_views, total_likes, total_comments])

    # Add headers for video details section
    print("Adding video details headers to Google Sheets...")
    sheet.append_row(["Publish Date", "Platform", "Video Title", "Views", "Likes", "Comments", "Tags"])

    # Append each video's data
    print(f"Adding {len(video_details)} videos to Google Sheets...")
    for video in video_details:
        sheet.append_row(video)

    # Append Mixcloud data
    print("Adding Mixcloud data to Google Sheets...")
    sheet.append_row(["Date", "Platform", "Followers", "Following", "Cloudcasts", "Favorites", "Listens"])
    for entry in mixcloud_data:
        sheet.append_row(entry)

    print("YouTube data added to Google Sheets.")
    print("Mixcloud data added to Google Sheets.")


if __name__ == "__main__":
    update_google_sheets()