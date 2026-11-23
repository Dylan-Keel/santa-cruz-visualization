import rasterio, numpy as np, cv2, sys
def g(n):
    a=rasterio.open(f'master/{n}_w.tif').read()
    return (a[0] if a.shape[0]==1 else cv2.cvtColor(np.moveaxis(a[:3],0,-1),cv2.COLOR_RGB2GRAY)).astype(np.float32)
hp=lambda a:cv2.GaussianBlur(a,(0,0),2)-cv2.GaussianBlur(a,(0,0),25)
def shifts(a,b,step=300,win=120,search=40):
    A=hp(a);B=hp(b);out=[]
    for y in range(win+search,a.shape[0]-win-search,step):
        for x in range(win+search,a.shape[1]-win-search,step):
            t=A[y-win:y+win,x-win:x+win]; s=B[y-win-search:y+win+search,x-win-search:x+win+search]
            if (a[y-win:y+win,x-win:x+win]==0).mean()>0.02 or (b[y-win-search:y+win+search,x-win-search:x+win+search]==0).mean()>0.02: continue
            r=cv2.matchTemplate(s,t,cv2.TM_CCOEFF_NORMED); _,mx,_,lc=cv2.minMaxLoc(r)
            if mx>0.35: out.append((lc[0]-search,lc[1]-search))
    o=np.array(out) if out else np.zeros((0,2)); 
    return len(o),(np.median(o,0).round(1).tolist() if len(o) else None),(float(np.median(np.hypot(o[:,0],o[:,1]))) if len(o) else None)
if __name__=='__main__':
    pairs=[('h1993','county_2005'),('h1970','h1993'),('h1966','h1970'),('h1962','h1966'),('h1958','h1962'),('h1954','h1958'),('h1948','h1954'),('h1942a','h1948'),('h1942b','h1948'),('h1966','county_2005')]
    for p,q in pairs: print(p,q,shifts(g(p),g(q)),flush=True)
