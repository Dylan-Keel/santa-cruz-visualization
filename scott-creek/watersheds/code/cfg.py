OX,OY=563000,4117000           # ref DEM origin (10 m, 1800 px); 4 km east of the first Scott Creek grid, same cell alignment
VW=(564500,4101200,576300,4113600); RW=2.5     # one view for all four watersheds, ~500 m buffer
VIEWS={'w':(VW,RW)}
def size(v,r): return int(round((v[2]-v[0])/r)),int(round((v[3]-v[1])/r))
VX=(563200,4099400,579600,4115600); RX=3.0     # wide backdrop for 3D and refinement
ALLV=dict(VIEWS); ALLV['x']=(VX,RX)
CEN=(568600.,4108500.)          # pose origin, unchanged so the first round of camera fits carries over
BX=(564000,4100000,580000,4116000)
