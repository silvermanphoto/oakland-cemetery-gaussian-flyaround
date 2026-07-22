# NOAA solar position algorithm (accurate ~0.01 deg). Pure stdlib.
import math
def julian_day(y,mo,d,h,mi,s):
    if mo<=2: y-=1; mo+=12
    A=y//100; B=2-A+A//4
    jd=math.floor(365.25*(y+4716))+math.floor(30.6001*(mo+1))+d+B-1524.5
    return jd+(h+mi/60.0+s/3600.0)/24.0
def sun_azel(y,mo,d,h,mi,s,lat,lon,tz):
    # local -> UTC
    jd=julian_day(y,mo,d,h,mi,s)-tz/24.0
    T=(jd-2451545.0)/36525.0
    L0=(280.46646+T*(36000.76983+T*0.0003032))%360.0
    M=357.52911+T*(35999.05029-0.0001537*T)
    e=0.016708634-T*(0.000042037+0.0000001267*T)
    Mr=math.radians(M)
    C=(1.914602-T*(0.004817+0.000014*T))*math.sin(Mr)+(0.019993-0.000101*T)*math.sin(2*Mr)+0.000289*math.sin(3*Mr)
    true_long=L0+C
    omega=125.04-1934.136*T
    lam=true_long-0.00569-0.00478*math.sin(math.radians(omega))
    eps0=23+(26+((21.448-T*(46.815+T*(0.00059-T*0.001813))))/60.0)/60.0
    eps=eps0+0.00256*math.cos(math.radians(omega))
    lamr=math.radians(lam)
    dec=math.degrees(math.asin(math.sin(math.radians(eps))*math.sin(lamr)))
    # equation of time
    y_=math.tan(math.radians(eps/2.0))**2
    L0r=math.radians(L0)
    Etime=4*math.degrees(y_*math.sin(2*L0r)-2*e*math.sin(Mr)+4*e*y_*math.sin(Mr)*math.cos(2*L0r)-0.5*y_*y_*math.sin(4*L0r)-1.25*e*e*math.sin(2*Mr))
    # true solar time (minutes)
    tst=(h*60+mi+s/60.0)+Etime+4*lon-60*tz
    ha=tst/4.0-180.0
    if ha< -180: ha+=360
    har=math.radians(ha); latr=math.radians(lat); decr=math.radians(dec)
    zen=math.degrees(math.acos(math.sin(latr)*math.sin(decr)+math.cos(latr)*math.cos(decr)*math.cos(har)))
    elev=90.0-zen
    # azimuth (clockwise from North)
    zenr=math.radians(zen)
    az_den=math.cos(latr)*math.sin(zenr)
    if abs(az_den)<1e-9: az=180.0
    else:
        ca=(math.sin(latr)*math.cos(zenr)-math.sin(decr))/az_den
        ca=max(-1,min(1,ca)); AC=math.degrees(math.acos(ca))
        az=(AC+180.0)%360.0 if ha>0 else (540.0-AC)%360.0
    # atmospheric refraction correction (approx) for low sun
    return az,elev,dec,Etime
lat,lon,tz=33.7496,-84.3720,-5.0
for label,(h,mi,s) in [("start 15:36:57",(15,36,57)),("mid  16:14:53",(16,14,53)),("end  16:52:49",(16,52,49))]:
    az,el,dec,eot=sun_azel(2022,12,22,h,mi,s,lat,lon,tz)
    print(f"{label} EST -> azimuth {az:6.2f} deg (cw from N), elevation {el:5.2f} deg   [dec {dec:.2f}, EoT {eot:.2f}min]")
