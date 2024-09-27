from dotenv import load_dotenv
import os

# Load the environment variables from .env file
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_IDS = [1243827508768411669, 1251336643479208057, 1250286391149985872, 1245836630007218280, 1228542670272729111, 1244602847916462151, 1248760011887218848, 1256809910084042835, 1244579462285103195, 1275195601172172820, 1250048544593936425, 1244071307973234799, 1245932555858083881]
MAIN_GUILD = int(os.getenv("MAIN_GUILD"))
IA_GUILD = int(os.getenv("IA_GUILD"))
DEV_GUILD = int(os.getenv("DEV_GUILD"))

LOG_EDIT_CHANNEL_ID = int(os.getenv("LOG_EDIT_CHANNEL_ID"))
LOG_DELETE_CHANNEL_ID  = int(os.getenv("LOG_DELETE_CHANNEL_ID"))
LOG_JOIN_VC = int(os.getenv("LOG_JOIN_VC"))
LOG_LEAVE_VC = int(os.getenv("LOG_LEAVE_VC"))
LOG_LEAVE_SERVER = int(os.getenv("LOG_LEAVE_SERVER"))

# Department Roles
All_Departments = 1243853158011109469
Development = 1243850650886864936
Media_Team = 1243843769682628678
State_Police = 1243832111559872512
Sheriffs_Office = 1243832161925333103
Police_Department = 1243834095948140615
Central_Dispatch = 1243843650811723807
Fire_Department = 1243843581559701556
Civilian = 1243873462469263462


# Define your COC Channels as a dictionary where keys are channel IDs and values are category names.
COC_Channels = {
    "MCSO Dev": [1262198472401227841, 1262198472401227842, 1262198472401227843, 1262198472401227844]
}

dep_info = {
    "MCSO": [
        """
        [MCSO Portal](https://sites.google.com/sokrpcommunity.com/sokrpmcsoportal/home?authuser=4)""",
        "https://cdn.discordapp.com/attachments/1261157824524849243/1269510104122916885/MCSO_Documents-01.png?ex=66cf4e2b&is=66cdfcab&hm=cb9c95e62f5aa53435ee93b1f8a19c598a21656d7ead14520f5ecd8d98f7b410&",
        "",
        "",
        "E74C3C"
    ],

    "MPD": ["""
        Welcome to the Municipal Police Department. Provided below are all department resources for use by MPD Personnel.\n
        **Primary Resources**
        [Department Portal](https://sites.google.com/view/municipal-police-department?usp=sharing)
        [Standard Operating Procedures](https://drive.google.com/file/d/1Sv7mE9RiMJUGaq9XS_oF7nHZy73H-nls/view)
        [Personnel Roster](https://docs.google.com/spreadsheets/d/1CnxCub-Na4TnRzG-Z_Ue7ZIY1MUpuG_c4uOWhGK1v8c/edit?usp=sharing)
        [Department Structures](https://docs.google.com/spreadsheets/d/1OBYTV3iKmD1dIn_571HeDz233l2CTKuNL6ozvcApN-c/edit?usp=sharing)
        [Promotion Guidelines](https://docs.google.com/document/d/1R19Jd5laEHHuscpBVWf_jF8p0Kc_okGC8WHwF38_Hfk/edit?usp=sharing)
        [MCCC Radio Traffic Guidelines](https://docs.google.com/document/d/17zVckwmCLHh_Bh8TKJaLCNvMyFqtrJnlcvhYtvCFoes/edit?usp=sharing)
        [MPD/MCSO Joint Policy List](https://docs.google.com/document/d/1QI9ARk43EKfQ2T03r6OKzUDEZ_zVWDBamFPcJwHxr2I/edit?usp=sharing)
        [Community 10 Code List](https://docs.google.com/document/d/1AB-f3vpJyPnsvrby1aD7dO2YeouEsiVGDnNY_YEUZKk/edit)\n
        **Department Policies**
        [Policy 001 - Patrol Districts](https://docs.google.com/document/d/1v9UkKMEm8fhOojvmXaNc1akpE5PAvM7-zGNiFwvIdZc/edit?usp=sharing)
        [Policy 002 - Use of Force](https://docs.google.com/document/d/10USqg-7hCwAH9J5h3WFDKL6YHFVaUSU6ioQc6Y10mzo/edit?usp=sharing)
        [Policy 003 - Officer Behavior](https://docs.google.com/document/d/1VcI0s_3hSrHuD5NVP2OSktC0lEDb0w0NAwJbmmDt4QE/edit?usp=sharing)
        [Policy 004 - Pursuit Policy](https://docs.google.com/document/d/1jNGd0INgqPAMVAfpxrm-4p7JowfX_aXuXUe5I2G9low/edit?usp=sharing)\n
        **Department Forms**
        [Policy Agreement Form](https://forms.gle/cMd9yoxXFMRHWtW77)
        [Roster Sign-up](https://forms.gle/ys2dL37m5AQxYxjLA)
        [Patrol Log](https://forms.gle/9W9z6QySUcU3v9Fe6)
        [Commendation Form](https://forms.gle/tWJVHopo2mJL6W146)
        [Complaint Form](https://forms.gle/NwRGZ8mG1LnVnAX58)
        [LOA Report Form](https://forms.gle/K3uXpRWqs7KKv94r5)
        [Feedback/Suggestion Form](https://forms.gle/b23K3G4ovYphNNxC8)""",
        "https://media.discordapp.net/attachments/971321037725769748/1273408269792317483/PD_Banner-01.png?ex=66cfa4de&is=66ce535e&hm=6560d96baa672cf10ad8b89b00d53c1288419d18925dfbbfcf70602b499f9911&format=webp&quality=lossless&width=788&height=197&",
        "https://media.discordapp.net/attachments/971321037725769748/1273405817256677457/wwwww_5.png?ex=66cfa295&is=66ce5115&hm=343ac465d4a54127f9c5915a853100acab6122bd57e6b47127e6e51fb388a15d&format=webp&quality=lossless&width=788&height=788&",
        "",
        "d48f02"
    ],

    "CIV": ["""
        The following is a reference document of publicly available Civilian Operations documentation. Civilian Operations members are expected to review all related documentation and have an understanding of it.
        *If you have questions or notice something that needs adding/fixing, reach out to <@&1248921836771868724>*.

        > General Department Documentation
        〢[Standard Operating Procedure](https://docs.google.com/document/d/1SdNHQ-4opqwHqGKUCcvzE-F7ywFkTpz1nHMhzoo7_LY/edit?usp=sharing)
        〢[Structures - Vehicles, Aircraft, Animals, Weapons](https://docs.google.com/spreadsheets/d/1e_IeVwEtqHsrv_fFATksqfUHkawQ6LWVLTGwii7P7Ws/edit?usp=sharing)
        〢[Department Public Roster](https://docs.google.com/spreadsheets/d/1yLdoxEGIOoxNxW3QcNgROfdlJnjeagT4GyPCZL1DKEw/edit?usp=sharing)
        〢[Activity Patrol Log](https://docs.google.com/forms/d/e/1FAIpQLSfOdDA2WYkdgON9PB9nbXAzCPohiM2quJHpHO_upOBi82yrbg/viewform)
        〢[Community LOA Form](https://docs.google.com/forms/d/e/1FAIpQLScbdODiPB9yCYD1KF3q3TNmaQYoGIXAgcnxVS9M3Si0UCzl8A/viewform)
        〢[Department Suggestion Form](https://docs.google.com/forms/d/e/1FAIpQLScKx363EO5f-ygznXsAO5QZmgFxNn3c1DSSC-9xb7zjGOeAzA/viewform)
        〢[Complaint Form - Civilian Membership](https://docs.google.com/forms/d/e/1FAIpQLSepcZciuKygcD4uamyKQCKrt46GaMbEdrvv1NRUWyeDgI-3wQ/viewform)

        > Divisions of Civilian Operations
        〢Kentucky Aviation Division - Division Operating Procedure [Coming Soon]
        〢[Organized Criminal Enterprises - Division Operating Procedure](https://docs.google.com/document/d/1TgwAWJfnMFZAw5tEolaRUJ4rVbqhd1ml70bXVU-2qSM/edit?usp=sharing)
        〢[Kentucky Chamber of Commerce - Business Operating Guidelines](https://docs.google.com/document/d/1IMHYsBrQPJ0wYsYdcI_afYQxUil15tZnJYXaX5Xot7o/edit?usp=sharing)

        > Community Documentation and Resources
        〢[SOKRP - Community Rules and Regulations](https://docs.google.com/document/d/1Rdgb-F8atDe44G3IXdDDNRE0dHRk9iUkkKU6ifvjwcI/edit#heading=h.y1v4nf5mykxc)
        〢[SOKRP - Community Rank Structure](https://docs.google.com/spreadsheets/d/1V1Ozrt_UX1w3ukidwGFCJXUJVIWhF4SsEe6OfZy7iMg/edit?gid=802449135#gid=802449135)""",
        "",
        "https://i.gyazo.com/df693124e8e811bc16eb3f53d9a19b95.png",
        "Civilian Operations - State of Kentucky Roleplay",
        "F8A65C"
    ],

    "KSP": [
        """
        # About us
        The Kentucky State Police promotes public safety through service, integrity, and professionalism utilizing partnerships to: Prevent, reduce, and deter crime and the fear of crime and enhance highway safety through education and enforcement. Safeguard property and protect individual rights. Our dedication and strict adherence to our core values and principles ensure that the Kentucky State Police will remain a detail-oriented, efficient, and professional law enforcement agency in service to the citizens of the Commonwealth of Kentucky.

        Kentucky State Police Portal
        [Website](https://sites.google.com/view/sokrp-state-police/home)

        Kentucky State Police Roster
        [Official Roster](https://docs.google.com/spreadsheets/d/19LaKxBUpKGhxMR9LUO0BteDohAiBaZTjBfxTOOUgquY/edit?gid=0)

        Kentucky State Police Complaint Form
        [Complaint Form](https://docs.google.com/forms/d/e/1FAIpQLSdR5pcoDCrToLrArqctOc0Tcp7pTEnfcr4qoTvHUEKQct_lfw/viewform)

        Kentucky State Police Commendation Form
        [Commendation Form](https://docs.google.com/forms/d/e/1FAIpQLSchFwEl3PZlT8Ys6gHIcGRuZlEixGUUVMdy_1194sDLW_pz4A/viewform)""",
        "https://media.discordapp.net/attachments/1252307383498047508/1261116631061630986/APPLY.gif?ex=66cf17a3&is=66cdc623&hm=93363f04c1fba19c800d1d8471b665ab58d8f9e13ab424b6dd688c373638fb6f&width=1244&height=622&",
        "https://media.discordapp.net/attachments/1252307383498047508/1260347118133051472/PD_Psd_2.png?ex=66cf96b9&is=66ce4539&hm=6a1ca3eee34ef9d0b705ca5caffb4ffc843ba5cec13af3e79def9eecd407ad86&format=webp&quality=lossless&width=622&height=622&",
        "",
        "9B59B6"
    ],
}

# API config
API = {
    "IP_ADDR": os.getenv("API_IP_ADDR"),
    "Port": os.getenv("API_PORT")
}