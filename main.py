import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
import requests

# Set up the scope and authorize the Google Sheets API
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/yt-analytics.readonly",
         "https://www.googleapis.com/auth/youtube.readonly", "https://www.googleapis.com/auth/youtube.force-ssl"]
creds = service_account.Credentials.from_service_account_file('credentials.json', scopes=scope)
client = gspread.authorize(creds)
sheet = client.open("BrixtonRadio").sheet1

# YouTube API Key and Channel ID for basic statistics
YOUTUBE_API_KEY = 'AIzaSyAwVM-HcfQx5QPp6emEGQZ4EuBpUaN6fSk'
CHANNEL_ID = 'UCAvtGQclGUkI14zeGw4_FpQ'

# Fetch YouTube channel profile data
def get_youtube_profile_data():
    url = f"https://www.googleapis.com/youtube/v3/channels?part=statistics&id={CHANNEL_ID}&key={YOUTUBE_API_KEY}"
    response = requests.get(url)
    data = response.json()

    if "items" in data and len(data["items"]) > 0:
        stats = data["items"][0]["statistics"]
        subscriber_count = int(stats["subscriberCount"])
        total_views = int(stats["viewCount"])
        video_count = int(stats["videoCount"])

        # Fetch the most-viewed video
        videos_url = f"https://www.googleapis.com/youtube/v3/search?key={YOUTUBE_API_KEY}&channelId={CHANNEL_ID}&part=id,snippet&order=viewCount&maxResults=1"
        videos_response = requests.get(videos_url)
        videos_data = videos_response.json()

        if "items" in videos_data and len(videos_data["items"]) > 0:
            video_id = videos_data["items"][0]["id"]["videoId"]

            # Get statistics for the most-viewed video
            video_stats_url = f"https://www.googleapis.com/youtube/v3/videos?key={YOUTUBE_API_KEY}&part=statistics,snippet&id={video_id}"
            video_stats_response = requests.get(video_stats_url)
            video_stats = video_stats_response.json()

            if "items" in video_stats and len(video_stats["items"]) > 0:
                video_statistics = video_stats["items"][0]["statistics"]
                video_title = video_stats["items"][0]["snippet"]["title"]
                video_views = int(video_statistics.get("viewCount", 0))
                video_likes = int(video_statistics.get("likeCount", 0))
                video_comments = int(video_statistics.get("commentCount", 0))
                
                return subscriber_count, total_views, video_count, video_title, video_views, video_likes, video_comments
    else:
        print("Error fetching data: ", data)
        return None, None, None, None, None, None, None

# Fetch YouTube Analytics data for demographics and engagement
def get_youtube_analytics_data():
    credentials = service_account.Credentials.from_service_account_file(
        'credentials.json',
        scopes=["https://www.googleapis.com/auth/yt-analytics.readonly"]
    )
    youtube_analytics = build('youtubeAnalytics', 'v2', credentials=creds)
    # Define the request for demographic and engagement data
    request = youtube_analytics.reports().query(
        ids="channel==MINE",
        startDate="2023-01-01",
        endDate=datetime.now().strftime("%Y-%m-%d"),
        metrics="viewerPercentage,averageViewDuration",
        dimensions="ageGroup,gender,country",
        filters="country==US",
        sort="-viewerPercentage",
        maxResults=10
    )
    
    # Execute the request
    response = request.execute()
    
    demographics_data = response.get("rows", [])
    
    return demographics_data

# Update Google Sheets with YouTube profile data and Analytics data
def update_google_sheets():
    # Get YouTube profile data
    subscribers, total_views, video_count, most_viewed_title, most_viewed_views, most_viewed_likes, most_viewed_comments = get_youtube_profile_data()
    # Get YouTube analytics demographics and engagement data
    demographics_data = get_youtube_analytics_data()

    # Write summary data to Google Sheets
    sheet.append_row(["Date", "Platform", "Subscribers", "Total Views", "Total Videos", "Most Viewed Video Title", "Views", "Likes", "Comments"])
    sheet.append_row([
        datetime.now().strftime("%Y-%m-%d"),
        "YouTube",
        subscribers,
        total_views,
        video_count,
        most_viewed_title,
        most_viewed_views,
        most_viewed_likes,
        most_viewed_comments
    ])

    # Add demographic data to Google Sheets
    sheet.append_row(["Age Group", "Gender", "Country", "Viewer Percentage", "Avg. View Duration", "Avg. Watch Time"])
    for row in demographics_data:
        sheet.append_row(row)

    print("YouTube data and demographics added to Google Sheets.")

if __name__ == "__main__":
    update_google_sheets()
