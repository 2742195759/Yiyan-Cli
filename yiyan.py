import asyncio
from pyppeteer import launch
import pyppeteer
import os
import time
from pyppeteer_stealth import stealth
import sys

def parameter_parser():
    import argparse
    parser = argparse.ArgumentParser(description="Support Args:")
    parser.add_argument("--query",                  type=str,   default="你好",  help="data path")
    parser.add_argument("--prompt",                 type=str,   default="no",  help="data path")
    parser.add_argument("--cookie",                 type=str,   help="data path")
    parser.add_argument("--proxy",                  type=str,   default=""  ,  help="data path")
    return parser.parse_args()

args = parameter_parser()
#from pyppeteer.launcher import Launcher
#print(' '.join(Launcher(headless=True, options={'args': ['--no-sandbox']}).cmd))

pyppeteer.launcher.DEFAULT_ARGS.remove("--enable-automation")

async def login_yiyan():
    browser = await launch(userDataDir=f"{args.cookie}", headless=False, options={'args': ['--no-sandbox', [f'--proxy-server={args.proxy}']], 'defaultViewport': {'width': 1920, 'height': 1080}})
    page = await browser.newPage()
    await stealth(page)  # <-- Here
    await page.goto('https://yiyan.baidu.com')
    #elems = await page.JJ('div.Qyj8AoQa')  # indirectly cause a navigation
    #await elems[0].click()
    time.sleep(5.0)
    element = await page.querySelector('div.Qyj8AoQa')
    await element.click()
    title = await page.evaluate('(element) => element.textContent', element)
    print(title)
    await element.click()
    await element.click()
    time.sleep(5.0)
    time.sleep(10.0)
    # 将这个文件通过 python upload 投射到服务器上，使用百度入流扫码登录
    await page.screenshot({'path': 'example.png'})
    breakpoint() 
    time.sleep(20.0)
    # 查看是否登录成功
    await page.screenshot({'path': 'example.png'})
    await browser.close()
    #print (json)


async def process(inp):
    browser = await launch(userDataDir=f"{args.cookie}", headless=False, options={'args': ['--no-sandbox', [f'--proxy-server={args.proxy}']], 'defaultViewport': {'width': 1920, 'height': 1080}})
    page = await browser.newPage()
    await stealth(page)  # <-- Here
    await page.evaluate("Object.defineProperties(navigator,{ webdriver:{ get: () => false } })", force_expr=True)
    await page.goto('https://yiyan.baidu.com')
    time.sleep(3.0)
    await page.click("span.dJ7XSrBC")
    time.sleep(3.0)

    # input the text and query yiyan.
    await page.type("textarea.wBs12eIN", inp, delay=20)
    await page.click("span.pa6BxUpp")
    time.sleep(20.0)
        
    # Extract the output from the page
    responses = await page.JJ("div.custom-html")
    #for response in responses:
    outputs = []
    for response in responses: 
        output = await page.evaluate('(element) => element.innerHTML', response)
        outputs.append(output)
    print(outputs[0])
    #await page.screenshot({'path': 'example.png'})

async def wait_output(page):
    tot_time = 120
    loop_time = 0.3
    for i in range(int(tot_time / loop_time)):
        time.sleep(loop_time)
        element = await page.querySelector(".pa6BxUpp")
        display_state = await page.evaluate("""(element) => window.getComputedStyle(element).display""", element)
        if display_state != "none": 
            # if display_state == none: generating.
            # if display_state == flex: means done.
            return True
    return False
    
async def process_loop(promote=True):
    browser = await launch(userDataDir=f"{args.cookie}", headless=True, options={'args': ['--no-sandbox'], 'defaultViewport': {'width': 1920, 'height': 1080}})
    page = await browser.newPage()
    await stealth(page)  # <-- Here
    await page.evaluate("Object.defineProperties(navigator,{ webdriver:{ get: () => false } })", force_expr=True)
    await page.goto('https://yiyan.baidu.com')
    time.sleep(3.0)
    await page.click("span.dJ7XSrBC")
    time.sleep(3.0)

    # input the text and query yiyan.
    while True:
        if promote: 
            print ("请输入你的文本：")
        try:
            inp = input()
        except:
            # EOF, Exit this subprocess.
            break
        if inp == "quit": 
            break

        await page.type("textarea.wBs12eIN", inp, delay=5)
        await page.click("span.pa6BxUpp")
        time.sleep(3.0)
        
        if await wait_output(page) == False: 
            print ("TimeOut")
        else:
            # Extract the output from the page
            responses = await page.JJ("div.custom-html")
            #for response in responses:
            outputs = []
            for response in responses: 
                output = await page.evaluate('(element) => element.innerHTML', response)
                outputs.append(render(output))
            to_output = [ line.strip("\n") for line in outputs[0].split("\n") if line.strip() != "" ]
            print("\n".join(to_output))
        print("") # empty line for seperating.
        sys.stdout.flush()
    await browser.close()
        #await page.screenshot({'path': 'example.png'})

from html.parser import HTMLParser
from html.entities import name2codepoint

class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        # lists of fields to be extracted
        self.stack = []
        
    def wrapper(self, tag, attrs, tmp_out):
        if 'class' in attrs and attrs['class'] in ['code-wrapper', 'code-copy-text', 'code-lang']: 
            return []
        if tag == "p": tmp_out.append("\n")
        if tag == "code": 
            if 'class' in attrs and 'language' in attrs['class']:
                family = attrs['class'].replace("language-", "")
                tmp_out[0:0] = f"```{family}\n"
                tmp_out.append("\n```")
            else: 
                tmp_out[0:0] = "```"
                tmp_out.append("```")
        return tmp_out

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.stack.append((tag, attrs))

    def extend_list(self, items):
        extended = []
        for out in items: 
            extended.extend(out)
        return extended

    def handle_endtag(self, tag):
        tmp_out = []
        finded = False
        while len(self.stack) > 0: 
            if isinstance(self.stack[-1], tuple) and self.stack[-1][0] == tag:
                tag, attrs = self.stack.pop()
                tmp_out = list(reversed(tmp_out))
                tmp_out = self.extend_list(tmp_out)
                tmp_out = self.wrapper(tag, attrs, tmp_out)
                self.stack.append(tmp_out)
                finded = True
                break
            else:
                out = self.stack.pop()
                if not isinstance(out, tuple):
                    """ <input> may not close. just ignore it.
                    """
                    tmp_out.append(out)
        if finded is False:
            raise Exception(f"Error: tag not closed. {tag}")

    def handle_data(self, data):
        self.stack.append(data)

    def handle_entityref(self, name):
        c = chr(name2codepoint[name])
        self.stack.append(c)

    def handle_charref(self, name):
        if name.startswith('x'):
            c = chr(int(name[1:], 16))
        else:
            c = chr(int(name))
        self.stack.append(c)

    def get_output(self):
        output = self.extend_list(self.stack)
        return "".join(output)

def render(innerhtml_content):
    """ render html content and return a ascii text. """
    with open("./render.log", "w") as fp :
        fp.write(innerhtml_content)
    parser = MyHTMLParser()
    parser.feed(innerhtml_content)
    return parser.get_output()

def test():
    print("".join(render("<p>hello</p>")))
    with open("/root/xkvim/text.html", "r") as fp :
        lines = fp.readlines()
    print("".join(render("".join(lines))))

#test()

#asyncio.get_event_loop().run_until_complete(login_yiyan())
#asyncio.get_event_loop().run_until_complete(process(args.query))
asyncio.get_event_loop().run_until_complete(process_loop(args.prompt == "yes"))
