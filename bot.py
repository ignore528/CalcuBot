import os
import ast
import logging
import operator as op
from uuid import uuid4

from telegram import InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.ext import Application, InlineQueryHandler, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TOKEN = os.environ["BOT_TOKEN"]

OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.Mod: op.mod,
    ast.FloorDiv: op.floordiv,
    ast.USub: op.neg,
    ast.UAdd: op.pos,
}


def safe_eval(node):
    if isinstance(node, ast.Expression):
        return safe_eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in OPS:
        left = safe_eval(node.left)
        right = safe_eval(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 100:
            raise ValueError("Power too large")
        return OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in OPS:
        return OPS[type(node.op)](safe_eval(node.operand))
    raise ValueError("Invalid expression")


def calculate(text):
    text = (
        text.replace("x", "*")
        .replace("X", "*")
        .replace("×", "*")
        .replace("÷", "/")
        .replace("^", "**")
    )
    result = safe_eval(ast.parse(text, mode="eval"))
    if isinstance(result, float):
        if result.is_integer():
            result = int(result)
        else:
            result = round(result, 8)
    return result


async def inline_calc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip()
    if not query:
        return

    try:
        result = calculate(query)
    except Exception:
        return

    results = [
        InlineQueryResultArticle(
            id=str(uuid4()),
            title=str(result),
            description=f"{result} = {query}",
            input_message_content=InputTextMessageContent(f"{result} = {query}"),
        ),
        InlineQueryResultArticle(
            id=str(uuid4()),
            title=query,
            description=f"{query} = {result}",
            input_message_content=InputTextMessageContent(f"{query} = {result}"),
        ),
    ]
    await update.inline_query.answer(results, cache_time=0)


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(InlineQueryHandler(inline_calc))
    logger.info("Bot चालू हो गया")
    app.run_polling(allowed_updates=[Update.INLINE_QUERY])


if __name__ == "__main__":
    main()
