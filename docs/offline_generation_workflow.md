# Offline generation workflow
# 离线生成工作流

Goal: Gemma generates new practice material offline. A human reviews every item. Only approved
items go on the website, which stays static: no live model calls, no running cost.
目标：用 Gemma 离线生成新的练习内容，每一条都经过人工审核，审核通过后才放上网站。网站始终是静态的，不实时调用模型，没有运行成本。

Status: planned. The scripts in steps 1-4 are still to be built (in Claude Code).
状态：计划中。第 1–4 步的脚本还没写，之后在 Claude Code 里完成。

---

## What gets generated
## 生成什么

A "variant" is a new version of an existing scenario. The checkpoints and sources stay the same; the patient changes.
"变体"是现有场景的一个新版本：检查点和来源不变，变的是病人。

Examples / 例子:
- s1: an at-risk man who is unsure and hesitant rather than in a hurry; his hidden concern is his job.
  s1：一位有风险的男性，不急着检测、反而犹豫不决；他的隐藏议题是工作。
- s2: the result is given to someone whose partner is not supportive.
  s2：伴侣不太支持的病人来拿结果。
- s3: the carer is the one with suicidal thoughts.
  s3：有自杀念头的是照护者本人。

Each variant is its own fictional person, with its own role card (canonical facts), its own guided turns and,
if needed, its own family sheet.
每个变体都是一个独立的虚构人物，有自己的角色卡（固定事实）、自己的引导模式对话，必要时还有自己的家属准备单。

---

## The five steps
## 五个步骤

### 1. Write a short spec (you) / 写一份简短的设定（你来写）
specs/<scenario>_<name>.yaml, a few lines: who the patient is, personality, hidden concern, companion.
在 specs/ 下写几行：病人是谁、什么性格、隐藏议题是什么、有没有陪同者。
Example / 例子:
    base: s1_pretest_counselling
    name: daniel_hesitant
    patient: man, 31, at 50% risk, unsure whether he wants to know
    hidden_concern: worried a result could affect his job
    companion: none

### 2. Generate (script calls Gemma) / 生成（脚本调用 Gemma）
    python3 scripts/generate_variant.py specs/s1_daniel_hesitant.yaml
Gemma receives: the base role card, checkpoints.yaml (unchanged), the base guided.yaml as a format example,
and strict rules (no new medical facts; mentor notes may only reuse the existing checkpoint feedback; no
self-harm methods or amounts). Output goes to drafts/<scenario>_<name>/: role_card.yaml, guided.yaml.
Gemma 会拿到：原场景的角色卡、不变的检查点、原引导模式作为格式范例，以及严格的规则（不新增医学事实；导师点评只能沿用已有检查点的反馈；不出现自伤方法或数量）。结果存进 drafts/ 文件夹。

### 3. Automatic checks (script, no model) / 自动检查（脚本完成，不用模型）
    python3 scripts/check_variant.py drafts/s1_daniel_hesitant
- The YAML is valid, and every turn has exactly one best, one partial and one poor option.
  格式正确，每一轮恰好有一个最好、一个一般、一个差的选项。
- Facts in the patient's lines match the role card (names, ages, numbers).
  病人台词里的事实和角色卡一致（名字、年龄、数字）。
- Banned content is absent: CAG ranges, doses or onset predictions in patient lines; self-harm methods or amounts.
  没有违禁内容：病人台词里不出现 CAG 范围、剂量、发病年龄预测，也不出现自伤方法或数量。
- Every mentor note matches an existing checkpoint or red flag, so each note keeps its source.
  每条导师点评都能对应到已有的检查点或红旗，所以都有来源。
Drafts that fail are regenerated or fixed before review.
没通过的草稿会重新生成或修改，然后才进入人工审核。

### 4. Human review (you) / 人工审核（你）
    python3 scripts/make_review_checklist.py drafts/s1_daniel_hesitant
This writes a Chinese review checklist in the usual format: each turn with its three options, the patient's
reply and the mentor note, plus the source links. Anything that differs from the base scenario is marked.
You tick [x] or write comments, as before.
生成和之前格式一样的中文审核清单：每一轮的三个选项、病人回应、导师点评和来源链接；和原场景不同的地方会标出来。你照常打勾或写批注。

### 5. Publish (script + you) / 发布（脚本 + 你）
    python3 scripts/promote_variant.py drafts/s1_daniel_hesitant
    python3 scripts/build_web_v2.py
The approved draft moves to scenarios/<scenario>/variants/<name>/ with "Reviewed by" filled in.
The website build picks up approved variants only; a trainee can choose a version or get one at random.
Then you push to GitHub, and the website link is updated.
审核通过的草稿会移到 scenarios/<场景>/variants/<名字>/，并填上"Reviewed by"。网站只收录审核通过的变体，学员可以自选版本，也可以随机抽一个。之后你推到 GitHub，网站链接同步更新。

---

## Rules that keep it safe
## 保证安全的规则

- drafts/ is never built into the website. Only scenarios/ is.
  drafts/ 里的内容永远不会出现在网站上，网站只读 scenarios/。
- No new clinical claims without a source. If a variant needs one, it goes into checkpoints.yaml first and is reviewed like before.
  没有来源的临床说法一律不加。如果变体确实需要，先加进 checkpoints.yaml，按原来的方式审核。
- Batches run off-peak, with a pause between requests, because the GPU is shared.
  显卡是实验室共用的，批量生成放在不忙的时间，请求之间留间隔。
- For the grant report: record how many drafts were generated, how many failed the automatic checks,
  and how many the reviewer accepted, changed or rejected. These numbers show how reliable the model is.
  为以后的报告做记录：生成了多少份草稿、多少份没通过自动检查、审核时多少份通过、修改或否决。这些数字本身就能说明模型有多可靠。
