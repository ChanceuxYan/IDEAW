""" Test Only
"""

import sys
import torch

sys.path.append("..")
from ideaw import IDEAW
from data.dataset import AWdataset, get_data_loader, infinite_iter

IDEAW = IDEAW("config.yaml")

dataset = AWdataset("../../Watermark/miniAWdata_pickle/stft.pkl")
loader = get_data_loader(dataset=dataset, batch_size=10, num_workers=0)
INF_loader = infinite_iter(loader)

data = next(INF_loader)
print(f"batch data shape: {data.shape}")


# embedding&extracting process test
## shape check
audio = torch.FloatTensor(data[0].float().unsqueeze(0)).to("cpu")
audio_stft = IDEAW.stft(audio)
msg = [1, 1, 1, 1, -1, -1, -1, -1, 1, 1, 1, 1, -1, -1, -1, -1]  # 16bit
lcode = [1, 1, 0, 0, 0, 1, 1, 1, 0, 0]  # 10bit
msg = torch.FloatTensor(torch.tensor(msg).float().unsqueeze(0)).to("cpu")
lcode = torch.FloatTensor(torch.tensor(lcode).float().unsqueeze(0)).to("cpu")
print(f"audio shape: {audio.shape}")
print(f"stft audio shape: {audio_stft.shape}")
print(f"msg&lcode shape: {msg.shape}&{lcode.shape}")


# embedding msg and lcode into 1 second chunk
chunk_size = 16000
chunk = audio[:, 0 : 0 + chunk_size]  # 1s

chunk_wmd = IDEAW.embed_msg(chunk, msg).detach().cpu()
print(f"watermarked audio shape: {chunk_wmd.shape}")

chunk_wmd_lcd = IDEAW.embed_lcode(chunk_wmd, lcode)
print(f"lcode embedded audio shape: {chunk_wmd_lcd.shape}")


# extracing lcode and msg from chunk_wmd_lcd
mid, extr_lcode = IDEAW.extract_lcode(chunk_wmd_lcd)
extr_lcode = extr_lcode.int().detach()
print(f"extracted lcode shape: {extr_lcode.shape}")
print(f"mid signal shape: {mid.shape}")

extr_msg = IDEAW.extract_msg(mid).int().detach().cpu().numpy()
print(f"extracted msg shape: {extr_msg.shape}")
