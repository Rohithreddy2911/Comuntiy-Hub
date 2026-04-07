import asyncio
import traceback
import chatbot

async def run():
    try:
        res = await chatbot.chat(language='Python', question_type='MCQ', difficulty='Easy', Numberofquestions='2')
        print('RESULT:', res)
    except Exception as e:
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(run())
