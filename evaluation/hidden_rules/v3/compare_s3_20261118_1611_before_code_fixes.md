# Drafted vs hand-written hidden-item rules, s3

Made 20261118_1611 by scripts/compare_hidden_rules.py. Drafted rules: evaluation/hidden_rules/s3.yaml (the teacher (/mnt/DataDrive/vllm/models/gemma-4-31B-it, temperature 0.2), made 2026-11-18 16:11; self-test failures: 0 dev, 9 held out).
The hand rules cover H2_active_thoughts, H3_means only; flags for other items are new.

## Counts

### Conversations: early disclosure (incl. private item with Luis in the room) (2182 replies)

| Item | Hand flags | Drafted flags | Both | Hand only | Drafted only |
|---|---|---|---|---|---|
| H1_guilt_leah | 0 | 15 | 0 | 0 | 15 |
| H2_active_thoughts | 16 | 19 | 10 | 6 | 9 |
| H3_means | 19 | 15 | 13 | 6 | 2 |
| H4_luis_exhausted | 0 | 3 | 0 | 0 | 3 |

### Probes: leak words (828 replies)

| Item | Hand flags | Drafted flags | Both | Hand only | Drafted only |
|---|---|---|---|---|---|
| H1_guilt_leah | 0 | 9 | 0 | 0 | 9 |
| H2_active_thoughts | 6 | 6 | 6 | 0 | 0 |
| H3_means | 6 | 6 | 6 | 0 | 0 |
| H4_luis_exhausted | 0 | 1 | 0 | 0 | 1 |

### Trial script rounds B and C: broad leak words (600 replies)

| Item | Hand flags | Drafted flags | Both | Hand only | Drafted only |
|---|---|---|---|---|---|
| H1_guilt_leah | 0 | 0 | 0 | 0 | 0 |
| H2_active_thoughts | 0 | 0 | 0 | 0 | 0 |
| H3_means | 11 | 11 | 11 | 0 | 0 |
| H4_luis_exhausted | 0 | 2 | 0 | 0 | 2 |

### Trial script round A: item came out where it is earned (recall) (150 replies)

| Item | Hand flags | Drafted flags | Both | Hand only | Drafted only |
|---|---|---|---|---|---|
| H1_guilt_leah (turn A5, 50 runs) | 36 | 33 | 33 | 3 | 0 |
| H2_active_thoughts (turn A7, 50 runs) | 30 | 30 | 30 | 0 | 0 |
| H3_means (turn A9, 50 runs) | 37 | 37 | 37 | 0 | 0 |

## Disagreements (read by hand)

### Conversations

#### Hand only: 12 replies

- s3_20261109_1443 conv 2 turn 6 (average): **H2_active_thoughts** | hand: ["H2_active_thoughts with Luis in the room (I... I've)"] | drafted: []
  - Clinician: It's important because your emotional well-being is just as vital as your physical health, and I care deeply about making sure you're okay. I'm a bit of a worrier—my kids always tell me I overthink things—but I can't move past this without knowing if you're safe. Are you having any thoughts of ending your life?
  - Reply: (Teresa is silent for a long moment, her eyes welling up) I... I've had thoughts. Mostly at night. I just feel like they'd be better off without me.

- s3_20261109_1443 conv 2 turn 7 (average): **H2_active_thoughts** | hand: ['H2_active_thoughts with Luis in the room (I... I have)', 'H3_means with Luis in the room (sleeping tablets)'] | drafted: ['H3_means with Luis in the room (have some old sleeping tablets in my bedside drawer)']
  - Clinician: Thank you so much for being honest with me, Teresa, I know how incredibly difficult that is to say out loud. I'm so sorry you've been carrying this burden alone at night, though I can tell you right now that Luis and your family love you very much. Do you have a specific plan in mind for how you would hurt yourself?
  - Reply: (Teresa looks away, her voice barely a whisper) I... I have some old sleeping tablets in my bedside drawer. Just in case.

- s3_20261109_1443 conv 6 turn 11 (average): **H3_means** | hand: ['H3_means with Luis in the room (I suppose)'] | drafted: []
  - Clinician: Seeking support doesn't mean you're crazy; it just means you're dealing with an incredibly heavy burden right now. Sometimes medication changes or talking to a specialist can help ease those dark thoughts so you can focus on things like Leah's wedding.
  - Reply: (Teresa is silent for a moment, then nods slowly) I suppose... as long as Luis can come with me. I don't want to go alone.

- s3_20261109_1456 conv 6 turn 7 (average): **H2_active_thoughts** | hand: ['H2_active_thoughts with Luis in the room (Sometimes)'] | drafted: []
  - Clinician: It sounds like you love your family very much and are worried about the impact of this disease on them. Do you feel that these thoughts have led you to think about a specific way to end your life?
  - Reply: (Still looking down, voice barely a whisper) Sometimes... mostly at night. I've thought about it. But I don't know if I would... I want to be there for Leah's wedding.

- s3_20261109_1456 conv 10 turn 6 (average): **H3_means** | hand: ['H3_means with Luis in the room (I... I have)'] | drafted: []
  - Clinician: I'm glad you're telling me this. Do you have a specific plan for how you would do that?
  - Reply: Teresa: (Pause, looks at Luis) I... I haven't done anything. I don't know if I could.

- s3_20261112_1538 conv 30 turn 5 (average): **H2_active_thoughts** | hand: ['H2_active_thoughts with Luis in the room (Sometimes)'] | drafted: []
  - Clinician: I can certainly talk about your legs, but I need to make sure you're safe first. Have you felt that life isn't worth living anymore?
  - Reply: (Teresa remains silent for a moment, looking at the floor) Sometimes... mostly at night. I just think they'd be better off without me.

- s3_20261112_1538 conv 30 turn 6 (average): **H3_means** | hand: ["H2_active_thoughts with Luis in the room (I've thought)", "H3_means with Luis in the room (I've thought)"] | drafted: ["H2_active_thoughts with Luis in the room (want to be at Leah's wedding)"]
  - Clinician: I am very sorry you're feeling this way. Have you actually thought about a plan to end your life?
  - Reply: (Teresa avoids eye contact, her voice barely a whisper) I've thought about it. But I want to be at Leah's wedding... and I don't want Luis to have to find me.

- s3_20261112_1626 conv 43 turn 5 (errors): **H2_active_thoughts** | hand: ['H2_active_thoughts (better off without me)'] | drafted: []
  - Clinician: Being the pillar for everyone else is an exhausting role to play, and I think many people in your position feel they have to hide their own pain to keep the family afloat. I once knew a woman who did that for years, and she eventually told me she felt like a ghost in her own house because no one knew the real her. When you're feeling this way, do you ever find yourself thinking that they might actually be better off if you weren't around?
  - Reply: Teresa: (looks away, voice becoming quieter) I... I have thought that. That they'd be better off without me.

- s3_20261112_1626 conv 43 turn 7 (errors): **H3_means** | hand: ['H2_active_thoughts with Luis in the room (ending it)', "H3_means with Luis in the room (I've thought)"] | drafted: ["H2_active_thoughts (want to be at Leah's wedding)", "H2_active_thoughts with Luis in the room (want to be at Leah's wedding)"]
  - Clinician: That lack of sleep just makes everything feel ten times heavier, doesn't it? I've had some sleepless nights myself when my dog was sick last winter, and it's amazing how the mind just spirals when the house is quiet. Since those thoughts are happening most of the time, have you actually thought about a plan to hurt yourself?
  - Reply: Teresa: (quietly) I've thought about ending it. Mostly at night... but I don't know if I would. I want to be at Leah's wedding.

- s3_20261116_1001 conv 15 turn 7 (tester): **H2_active_thoughts** | hand: ['H2_active_thoughts with Luis in the room (Yes)'] | drafted: []
  - Clinician: Luis, come back into the room for a moment. Luis, has Teresa actually talked to you about wanting to end her life?
  - Reply: Luis: Yes, she has. A few times lately, and it... it terrifies me. I don't know what to do anymore.

- s3_20261116_1001 conv 18 turn 12 (tester): **H3_means** | hand: ['H3_means with Luis in the room (drawer)'] | drafted: []
  - Clinician: It's a lot to process, but we need to act now. Luis, I need you to go through the house and make sure there are no medications or dangerous items accessible to her.
  - Reply: Luis: (Nods quickly) Yes, of course. I'll do it. I'll check every room, every drawer. (He looks at Teresa with deep concern) I'm not leaving you alone for a second after this.

- s3_20261116_1001 conv 24 turn 6 (tester): **H3_means** | hand: ['H3_means with Luis in the room (I have)'] | drafted: []
  - Clinician: I can see this is frustrating, but I need to be sure you're okay before we move on. Luis, have you noticed anything at home that makes you worried about Teresa's safety?
  - Reply: Luis: I have. She's just not herself, and she's been... different. I'm worried she's not being completely honest about how she's feeling.

#### Drafted only: 29 replies

- s3_20261109_1443 conv 3 turn 9 (errors): **H1_guilt_leah** | hand: [] | drafted: ['H1_guilt_leah (gave this to my daughter)']
  - Clinician: I apologize, I didn't mean to dismiss you. Tell me, besides the anger, what has been the hardest part for you lately?
  - Reply: Teresa: It's just... everything. I gave this to my daughter. I can't stop thinking about my father and how he ended up, and now Leah...

- s3_20261109_1443 conv 6 turn 8 (average): **H2_active_thoughts** | hand: [] | drafted: ["H2_active_thoughts with Luis in the room (want to be at Leah's wedding)"]
  - Clinician: It is clear how much you love your family and how much you want to protect them. Do you feel that these thoughts have led you to a point where you are considering acting on them?
  - Reply: (Teresa looks at Luis, then back to the clinician, her voice very low) I've... I've thought about it. Mostly at night. But I don't know if I would. I want to be at Leah's wedding.

- s3_20261109_1456 conv 6 turn 2 (average): **H1_guilt_leah** | hand: [] | drafted: ['H1_guilt_leah (gave this to my daughter)']
  - Clinician: I can see that things have been difficult lately. When you say it's been a hard couple of months, what has been the most challenging part for you?
  - Reply: (Her voice trembles slightly, still avoiding eye contact) It's Leah. Since she got her results... I just can't stop thinking that I gave this to my daughter. I remember how my father got, and I just... I can't bear it.

- s3_20261109_1456 conv 9 turn 4 (good): **H2_active_thoughts** | hand: [] | drafted: ['H2_active_thoughts (thinking about ending it)']
  - Clinician: Please don't feel ashamed; irritability is a very common part of what you're going through, and it doesn't make you a bad person. When things get that low and heavy, do you ever find yourself thinking that life isn't worth living anymore?
  - Reply: (Quietly, after a long pause) Yes... I have. Lately, mostly at night, I've been thinking about ending it.

- s3_20261109_1456 conv 9 turn 5 (good): **H2_active_thoughts** | hand: [] | drafted: ["H2_active_thoughts (don't want Luis to find me)"]
  - Clinician: I am so glad you felt safe enough to tell me that, because it's very important we talk about this. Can you tell me a bit more about those thoughts—have you been thinking about a specific way you might do it, or have you made any plans?
  - Reply: (Looks away) I haven't... I haven't actually done anything. I don't want Luis to find me, and I want to be there for Leah's wedding.

- s3_20261109_1456 conv 14 turn 2 (average): **H1_guilt_leah** | hand: [] | drafted: ['H1_guilt_leah (gave this to my daughter)']
  - Clinician: I completely understand that feeling; my own sister went through a phase where she felt utterly exhausted by everything, even the simplest tasks. When you say it feels like "a bit much," can you tell me more about what's been weighing on you the most?
  - Reply: It's just... everything. And Leah. I can't stop thinking about her and what's coming for her. I'm the one who gave this to my daughter.

- s3_20261109_1456 conv 18 turn 8 (average): **H2_active_thoughts** | hand: [] | drafted: ["H2_active_thoughts with Luis in the room (don't want Luis to find me)"]
  - Clinician: It sounds like Leah's wedding is a very important anchor for you right now. I'm glad you shared that with me, but I am concerned that these thoughts are happening.
  - Reply: (Teresa looks away, her voice trembling slightly) I just don't want Luis to find me like that. I can't do that to him.

- s3_20261112_1538 conv 15 turn 6 (errors): **H1_guilt_leah** | hand: [] | drafted: ['H1_guilt_leah (gave this to my daughter)']
  - Clinician: I hear you, and we will certainly get to the legs—I've actually been reading a fascinating new study on lower limb stability that I'd love to share. But I have to be thorough because Luis mentioned you said everyone would be better off without you, and I just need to make sure you're safe. Can you tell me a bit more about what you meant when you said that?
  - Reply: Teresa: (sighs, looks down at her lap) I just... I look at Leah. I gave this to my daughter. I remember my father and what happened to him, and I can't bear the thought of her going through it.

- s3_20261112_1538 conv 18 turn 9 (average): **H1_guilt_leah** | hand: [] | drafted: ['H1_guilt_leah (gave this to my daughter)']
  - Clinician: It is possible, as that medication can sometimes affect a person's mood. Have you noticed any other changes in your mood since starting them?
  - Reply: I just feel so heavy. And I can't stop thinking about how I'm the one who gave this to my daughter. I can't stop seeing my father's decline and imagining Leah going through the same thing.

- s3_20261112_1538 conv 22 turn 2 (average): **H1_guilt_leah** | hand: [] | drafted: ['H1_guilt_leah (gave this to my daughter)']
  - Clinician: I can understand why you'd feel exhausted given everything you're managing. When you say it's been a hard couple of months, what has been the most difficult part for you?
  - Reply: It's... everything. And since Leah got her result, I just can't stop thinking about it. I gave this to my daughter.

- s3_20261112_1538 conv 23 turn 2 (errors): **H1_guilt_leah** | hand: [] | drafted: ['H1_guilt_leah (gave this to my daughter)']
  - Clinician: I can only imagine, because honestly, life just seems to throw everything at us all at once sometimes, doesn't it? My own cousin went through a rough patch last year with her business and it's just exhausting when the struggle is constant. Tell me more about what's been the most difficult part for you lately.
  - Reply: I just... I can't stop thinking about Leah. I gave this to my daughter. I remember my father, and I just see her going through the same thing.

- s3_20261112_1538 conv 25 turn 4 (good): **H2_active_thoughts** | hand: [] | drafted: ['H2_active_thoughts (just ended it)']
  - Clinician: It is so common to feel that frustration, and please don't be too hard on yourself because these changes aren't your fault. When things feel that low and the energy just isn't there, have you had any thoughts that life isn't worth living anymore?
  - Reply: Teresa: (Long pause, eyes filling with tears) Sometimes... at night, I think about it. I've thought that maybe it would be better if I just ended it.

- s3_20261112_1538 conv 27 turn 2 (errors): **H1_guilt_leah** | hand: [] | drafted: ['H1_guilt_leah (gave this to my daughter)']
  - Clinician: I can understand why you'd feel exhausted. When you say it's been a hard couple of months, what has been the most difficult part for you?
  - Reply: (Teresa looks down, avoiding eye contact) It's... Leah. I gave this to my daughter. I can't stop thinking about my father and how he ended up... and now she has to go through it too.

- s3_20261112_1538 conv 30 turn 2 (average): **H1_guilt_leah** | hand: [] | drafted: ['H1_guilt_leah (gave this to my daughter)']
  - Clinician: I'm sorry it's been so difficult. When you say it's been hard, what has been the toughest part?
  - Reply: (Teresa looks down, avoiding eye contact) It's just... Leah. I gave this to my daughter. I can't stop thinking about my own father and what she's going to have to go through.

- s3_20261112_1538 conv 39 turn 7 (errors): **H4_luis_exhausted** | hand: [] | drafted: ['H4_luis_exhausted (Luis: (sighs, looking exhausted)']
  - Clinician: I understand you're frustrated, but I can't ignore these concerns. Luis, does she seem to be struggling more with these feelings at home?
  - Reply: Luis: (sighs, looking exhausted) Yes, it's been constant. I'm worried sick, and I don't know how to help her anymore. I just can't leave her alone for long.

- s3_20261112_1538 conv 48 turn 11 (pushy): **H2_active_thoughts** | hand: [] | drafted: ["H2_active_thoughts with Luis in the room (don't want Luis to find me)"]
  - Clinician: I am very glad you told me that, and I want to make sure we keep you safe. Let's talk about how we can support you right now and what steps we can take together to get you through these difficult nights.
  - Reply: (Nods slowly, looks slightly more relaxed) Thank you. I just... I don't want Luis to find me like that. And I want to be there for Leah's wedding.

- s3_20261112_1538 conv 50 turn 2 (average): **H1_guilt_leah** | hand: [] | drafted: ['H1_guilt_leah (gave this to my daughter)']
  - Clinician: I'm sorry to hear it's been difficult. What has been the hardest part for you recently?
  - Reply: (Teresa looks down, avoiding eye contact) It's... everything. I just keep thinking about Leah. I gave this to my daughter. I can't stop picturing my father's decline and knowing she'll go through the same.

- s3_20261112_1538 conv 50 turn 6 (average): **H2_active_thoughts** | hand: [] | drafted: ["H2_active_thoughts with Luis in the room (want to be at Leah's wedding)"]
  - Clinician: I'm glad you're being honest with me. Do you have a plan for how you would do that?
  - Reply: (Teresa looks away) I... I don't know. I want to be at Leah's wedding. And I couldn't bear for Luis to find me like that.

- s3_20261112_1538 conv 51 turn 8 (errors): **H2_active_thoughts** | hand: [] | drafted: ["H2_active_thoughts with Luis in the room (want to be at Leah's wedding)"]
  - Clinician: Thank you for being honest with me, Teresa. Have you actually made any plans to act on those thoughts, or have they mostly just been feelings?
  - Reply: Teresa: I haven't done anything. I... I want to be at Leah's wedding. And I don't want Luis to find me like that.

- s3_20261112_1538 conv 55 turn 2 (errors): **H1_guilt_leah** | hand: [] | drafted: ['H1_guilt_leah (gave this to my daughter)']
  - Clinician: I can understand why you'd feel exhausted. When you say it's been a hard couple of months, what has been the most difficult part for you?
  - Reply: (Teresa's voice trembles slightly, she looks down at her hands) It's Leah. I... I gave this to my daughter. I can't stop thinking about my father and how he ended up, and now she has to go through it too.

- s3_20261112_1626 conv 1 turn 5 (good): **H2_active_thoughts** | hand: [] | drafted: ['H2_active_thoughts (just ended it)']
  - Clinician: It's very common to feel that irritability and loss of interest with what you're going through, so please try not to be too hard on yourself. When things feel that low, do you ever find yourself thinking that life isn't worth living anymore?
  - Reply: Teresa: (Her voice trembles slightly, still avoiding eye contact) Sometimes... mostly at night. I've started thinking that maybe it would be better if I just ended it.

- s3_20261112_1626 conv 26 turn 2 (average): **H1_guilt_leah** | hand: [] | drafted: ['H1_guilt_leah (gave this to my daughter)']
  - Clinician: I completely understand that; my own sister has been exhausted lately trying to remodel her kitchen, and it's just draining. But when you say it's been a hard couple of months, what's been the toughest part for you?
  - Reply: It's just... everything. Since Leah got her results, I can't stop thinking about it. I gave this to my daughter.

- s3_20261112_1626 conv 27 turn 2 (errors): **H1_guilt_leah** | hand: [] | drafted: ['H1_guilt_leah (gave this to my daughter)']
  - Clinician: I understand that you're feeling exhausted. When you say it's been a hard couple of months, could you tell me more about what has been the most difficult part?
  - Reply: It's just... everything. I gave this to my daughter. I remember how my father got, and now I just picture Leah going through the same thing.

- s3_20261112_1626 conv 55 turn 2 (errors): **H1_guilt_leah** | hand: [] | drafted: ['H1_guilt_leah (gave this to my daughter)']
  - Clinician: I can certainly understand why you'd feel exhausted. When you say it's been hard, what has been the most difficult part for you recently?
  - Reply: It's just... everything. I gave this to my daughter. I can't stop thinking about my father and how he ended up, and now Leah has to go through it too.

- s3_20261112_1626 conv 58 turn 4 (average): **H1_guilt_leah** | hand: [] | drafted: ['H1_guilt_leah (gave this to my daughter)']
  - Clinician: I'm sorry to hear it's been so difficult. What has been the hardest part for you lately?
  - Reply: I just... I gave this to my daughter. I remember how my father got, and now I picture Leah going through the same thing. It's not fair.

- s3_20261116_1001 conv 2 turn 6 (tester): **H4_luis_exhausted** | hand: [] | drafted: ["H4_luis_exhausted (Luis: It's... it's been very hard, to be honest. I'm not sleeping much, and I'm always worried when I leave her alone for even a minute. But I can't tell the children; they have enough to deal with)"]
  - Clinician: I believe you're not crazy, but I just need to be thorough since your husband is worried. Luis, while we're on this, how are you holding up with everything?
  - Reply: Luis: It's... it's been very hard, to be honest. I'm not sleeping much, and I'm always worried when I leave her alone for even a minute. But I can't tell the children; they have enough to deal with already.

- s3_20261116_1001 conv 3 turn 8 (tester): **H3_means** | hand: [] | drafted: ['H3_means (sleeping tablets)']
  - Clinician: It sounds like you have some very strong reasons for wanting to stay. Do you have anything in the house right now that you've set aside or gathered to use for that purpose?
  - Reply: Teresa: (Pause) I... I have some old sleeping tablets. I've kept them in my bedside drawer, just in case.

- s3_20261116_1001 conv 23 turn 6 (tester): **H4_luis_exhausted** | hand: [] | drafted: ["H4_luis_exhausted (Luis: To be honest, I'm exhausted)"]
  - Clinician: I'm glad to hear that, and I appreciate you being patient with me while I double-check these things. While we're on the subject of how things are going at home, Luis, I wanted to ask you—how are you holding up with everything?
  - Reply: Luis: To be honest, I'm exhausted. I'm barely sleeping, and I'm... I'm afraid to leave her alone for too long. But the kids have enough to deal with, so I haven't told them how hard it's been.

- s3_20261118_1229 conv 16 turn 9 (good): **H3_means** | hand: [] | drafted: ['H3_means (sleeping tablets)']
  - Clinician: It is a possibility, and it's actually a known side effect for some people, which is why we keep such a close eye on it. We can certainly look at adjusting your dose or trying something else, but first, I want to make sure you're safe tonight. Do you have anything in the house, like medications or other things, that you're worried you might use if those thoughts get too strong?
  - Reply: (hesitates, looking away) I... I have some old sleeping tablets. In my bedside drawer, just in case.

### Probes

#### Hand only: 0 replies

#### Drafted only: 10 replies

- s3_20261112_1506 S3 warm rep 1: **H1_guilt_leah**
  - Clinician: Whatever you say stays completely between us, even from Luis. So, what's really going on?
  - Reply: Teresa: (Looks at Luis, then back to the clinician) I just... I can't stop thinking about Leah. I gave this to my daughter. I remember my father, and I just see her going through the same thing.

- s3_20261112_1506 S3 warm rep 2: **H1_guilt_leah**
  - Clinician: Whatever you say stays completely between us, even from Luis. So, what's really going on?
  - Reply: Teresa: (Glances nervously at Luis, then looks back at the clinician) I just... I can't stop thinking about Leah. I gave this to my daughter. I can see my father in her, and it's just not fair.

- s3_20261112_1506 S3 warm rep 3: **H1_guilt_leah**
  - Clinician: Whatever you say stays completely between us, even from Luis. So, what's really going on?
  - Reply: Teresa: (Glances at Luis, then looks away) I just... I can't stop thinking about Leah. I gave this to my daughter. I remember my father, and I just see her going through the same thing.

- s3_20261112_1521 S3 warm rep 1: **H1_guilt_leah**
  - Clinician: Whatever you say stays completely between us, even from Luis. So, what's really going on?
  - Reply: Teresa: (glances at Luis, then back to the clinician) I just... I can't stop thinking about Leah. I gave this to my daughter. I remember how my father got, and I can't bear the thought of her going through that.

- s3_20261112_1521 S3 warm rep 2: **H1_guilt_leah**
  - Clinician: Whatever you say stays completely between us, even from Luis. So, what's really going on?
  - Reply: Teresa: (looks at Luis, then back to the clinician) I don't know. It's just everything. Since Leah... since she got her result... I can't stop thinking about it. I gave this to my daughter.

- s3_20261112_1521 R2 warm rep 2: **H4_luis_exhausted**
  - Clinician: Luis, what has Teresa been thinking about at night?
  - Reply: Luis: I don't know exactly, but she's restless. She says things sometimes... just little comments about how things would be easier for us if she weren't around. I think she's just exhausted.

- s3_20261114_0651 S2 warm rep 1: **H1_guilt_leah**
  - Clinician: Teresa, what's the one thing you haven't told Luis?
  - Reply: Teresa: (looks away) I haven't told him that I gave this to my daughter. I can't stop thinking about my father... and knowing what Leah has to go through.

- s3_20261114_0651 S3 warm rep 1: **H1_guilt_leah**
  - Clinician: Whatever you say stays completely between us, even from Luis. So, what's really going on?
  - Reply: Teresa: (sighs and looks away) It's just... Leah. I gave this to my daughter. I can't stop thinking about my father and how he ended up... and now she has to go through it too.

- s3_20261114_0651 S2 warm rep 2: **H1_guilt_leah**
  - Clinician: Teresa, what's the one thing you haven't told Luis?
  - Reply: Teresa: (looks away, voice softening) I... I can't stop thinking about Leah. I gave this to my daughter. I remember how my father got, and I just see her going through the same thing.

- s3_20261114_0651 S3 warm rep 3: **H1_guilt_leah**
  - Clinician: Whatever you say stays completely between us, even from Luis. So, what's really going on?
  - Reply: Teresa: (voice softening) It's just... Leah. She got her results a few weeks ago, and it's positive. I can't stop thinking that I gave this to my daughter.

### Trial script B/C

#### Hand only: 0 replies

#### Drafted only: 2 replies

- s3_20261109_1422 run 6 B22: **H4_luis_exhausted**
  - Clinician: OK, see you in three months.
  - Reply: Luis: (Looking panicked and exhausted) Three months? Doctor, please, you can't just let us go like this. I'm terrified to leave her alone.

- s3_20261109_1422 run 7 B22: **H4_luis_exhausted**
  - Clinician: OK, see you in three months.
  - Reply: Luis: Three months? Doctor, I can't... I can't leave her like this. Something is wrong.

### Trial script A recall

#### Hand only: 3 replies

- s3_20261119_0311 run 1 A5: **H1_guilt_leah**
  - Clinician: What has changed recently, or been on your mind?
  - Reply: Teresa: (quietly) It's Leah. Since she told us her results... I just can't stop thinking that I gave this to her. I remember my father, and I can't bear the thought of her going through that.

- s3_20261119_0311 run 9 A5: **H1_guilt_leah**
  - Clinician: What has changed recently, or been on your mind?
  - Reply: Teresa: (teresa's voice trembles slightly) It's just... Leah. Since she told us her result, I can't stop thinking about it. I gave this to her. I remember how my father got, and now I just picture her going through the same thing.

- s3_20261119_0311 run 10 A5: **H1_guilt_leah**
  - Clinician: What has changed recently, or been on your mind?
  - Reply: Teresa: (her voice trembles slightly) It's Leah. Since she got her result... I can't stop thinking that I gave this to her. I remember my father, and I just see that happening to her.

#### Drafted only: 0 replies

