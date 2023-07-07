import asyncio
from pyppeteer import launch
import pyppeteer
import os
import time
from pyppeteer_stealth import stealth
import sys
import copy

# NOTE: update the chromium version.
pyppeteer.__chromium_revision__ = '1000260' # can't remote debug with default version, this version is 2022.10 version
pyppeteer.launcher.DEFAULT_ARGS.remove("--enable-automation")

def parameter_parser():
    import argparse
    parser = argparse.ArgumentParser(description="Support Args:")
    parser.add_argument("--query",                  type=str,   default="你好",  help="data path")
    parser.add_argument("--prompt",                 type=str,   default="no",  help="data path")
    parser.add_argument("--cookie",                 type=str,   help="data path")
    parser.add_argument("--proxy",                  type=str,   default=""  ,  help="data path")
    parser.add_argument("--login",                  type=str,   default="no"  ,  help="data path")
    parser.add_argument("--debug",                  type=str,   default="no"  ,  help="data path")
    return parser.parse_args()

# NOTE: change this when web version update.
text_area_class = "wBs12eIN"
send_area_class = "VAtmtpqL"

cmd_args = parameter_parser()
if cmd_args.debug == "yes": 
    """
    Step1: 
        Visit http://10.255.125.22:8086/json/list to get frontendURI
    Step2: 
        Visit http://10.255.125.22:8086/{DevToolFrontendURL} to access the remote debugging. 

    Useful for login and record cookies.

    If you want to use http_proxy.py and you want to access it from outside: 
    Step1: 
        change: search `server` and change it to `127.0.0.1:10000` if your chrome listen in 0.0.0.0:10000
    Step2: 
        add listen port and expose it by docker.
    """
    pyppeteer.launcher.DEFAULT_ARGS.append("--remote-debugging-port=10000")
    pyppeteer.launcher.DEFAULT_ARGS.append("--remote-debugging-address=0.0.0.0")
    from pyppeteer.launcher import Launcher
    print(' '.join(Launcher(userDataDir=f"{cmd_args.cookie}", headless=True, options={'args': ['--no-sandbox'], 'defaultViewport': {'width': 1920, 'height': 1080}}).cmd))

def do_every(total, every):
    for i in range(int(total / every)): 
        time.sleep(every)
        yield i

async def interact():
    """
    Console debug and interact with the browser, contain the following commands:
        - click selector
        - input selector text
        - show 
        - sleep
        - quit
    the output is a screenshot of the page.
    Useful for debug while RemoteDebugging is not available.
    """
    env = copy.deepcopy(os.environ)
    env.update({
        "http_proxy": "http://172.19.57.45:3128", 
        "https_proxy": "http://172.19.57.45:3128"})

    browser = await launch(userDataDir=f"{cmd_args.cookie}", headless=True, options={'args': ['--no-sandbox'], 'defaultViewport': {'width': 1920, 'height': 1080}})
    page = await browser.newPage()
    await stealth(page)  # <-- Here
    print ("start navigate to https://yiyan.baidu.com...")
    await page.goto('http://yiyan.baidu.com/')
    time.sleep(10)

    while True:
        next_instruction = input("(chrome) ")
        try:
            if next_instruction == "quit": 
                break

            elif next_instruction == "show": 
                pass

            elif next_instruction == "sleep":
                time.sleep(5)

            elif next_instruction.startswith("click"): 
                _, selector = next_instruction.split(" ")
                element = await page.querySelector(f'{selector}')
                await element.click()
                time.sleep(5)

            elif next_instruction.startswith("input"): 
                _, selector, text = next_instruction.split(" ")
                await page.type(f"{selector}", f"{text}", delay=5)
                time.sleep(5)

            else: 
                print("Invalid key, just show.")
        except Exception as e:
            print(f"Error {e}, just show")
        await page.screenshot({'path': 'example.png'})
    await browser.close()


async def wait_output(page):
    tot_time = 120
    loop_time = 0.3
    for i in range(int(tot_time / loop_time)):
        time.sleep(loop_time)
        element = await page.querySelector(f".{send_area_class}")
        display_state = await page.evaluate("""(element) => window.getComputedStyle(element).display""", element)
        if display_state != "none": 
            # if display_state == none: generating.
            # if display_state == flex: means done.
            return True
    return False
    
async def process_loop(promote=True):
    browser = await launch(userDataDir=f"{cmd_args.cookie}", headless=True, options={'args': ['--no-sandbox'], 'defaultViewport': {'width': 1920, 'height': 1080}})
    page = await browser.newPage()
    await stealth(page)  # <-- Here
    await page.evaluate("Object.defineProperties(navigator,{ webdriver:{ get: () => false } })", force_expr=True)
    await page.goto('https://yiyan.baidu.com')
    time.sleep(5.0)
    await page.screenshot({'path': 'example.png'})

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

        await page.type(f"textarea.{text_area_class}", inp, delay=5)
        await page.click(f"span.{send_area_class}")
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
        if 'class' in attrs and attrs['class'] in ['code-copy-text', 'code-lang']: 
            return []
        if tag == "tr": tmp_out.append("\n")
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

if cmd_args.login == "yes": 
    asyncio.get_event_loop().run_until_complete(interact())
else: 
    asyncio.get_event_loop().run_until_complete(process_loop(cmd_args.prompt == "yes"))