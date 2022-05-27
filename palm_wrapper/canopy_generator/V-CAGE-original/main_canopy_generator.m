% madeline make autocorrelation length 10?
% mean LAI can be a parameter
% mean std should be set, play with it a little. maybe start with 1/4






%This program and all its subroutines were made by Gil Bohrer, 2006.
%They are introduced and explained in: Bohrer Wolosin Brady and Avissar
%2007 Tellus 59B, 566�576
%This program is the intellectual property of Gil Bohrer.
%It is free for academic use. Do not make any commercial use of this program.
%Please refer to the manuscript by Bohrer et al. 2007 Tellus (above) in any publication that is based on this program or that has used it to. 
% Copyright: Gil Bohrer and Roni avissar

%****************************** input parameters ***************************
% Domain parameters:
nx=250; % #grid points east-west 
ny=250;  % #grid points south-north                
Dx = 5.0; % horizontal grid-mesh size [m]. LoadCanopy_Profiles.m assumes Dx==Dy, this can be easily modified
Dy = Dx;
Dz= 3.0;  % vertical grid-mesh size [m], needed to find the highest point in the canopy, in terms of # grid-points, which is sometimes used to dimensionalize input arrays in a program that might use this canopy 

% Landscape parameters:
L=10.0; % length-scale of discontinuity [m] that characterizes patch-type distribution (regioal lenght-scale)

%patch params
PatchCutOff=[0.9 0.1]; %vector- portion of the area with each patch type -in this example; 90% Spring hardwood, 10% grass; Must total to 1!!! 
patchtype=[1 2]; %patch type code to patch canopy properties data in ForestCanopy_data.m 
%The user should add his/her patch types in ForestCanopy_data.m, as needed for their symulations and as observed in their environments 


%other params:
filepath = './OutFiles/'; %path to location of output files
%*******************************************************************

%Basic housekeeping
rand('state',sum(100*clock)); %randomize
npatch=length(patchtype);  %determine number of patch types

%normalized PatchCutOff and convert to accumulated area
PatchCutOff = PatchCutOff/sum(PatchCutOff);
if npatch > 1
    for p=2:npatch
        PatchCutOff(p)=PatchCutOff(p-1)+PatchCutOff(p);
    end
end

%build meshed-grid
x=[-(nx-1)/2:(nx-1)/2]*Dx;  
y=[-(ny-1)/2:(ny-1)/2]*Dy;
[X,Y] = meshgrid(x,y);

%Start V-Cage Simulation
% calculate patch-type map
if npatch > 1
    %Generate landscape map of patches
    AcF=exp(-(1/L)*(X.^2+Y.^2).^0.5); %regional (patch level) autocorrelation function. Could be replaced by an observed auto-correlation function, or patch type map
    lambda_r = Make_VCaGe_rand_field(X,Y,nx,ny,Dx,Dy,AcF);
    [patch] = Generate_PatchMap(patchtype,lambda_r,ny,nx,PatchCutOff,npatch);
    
    %Allocate canopy properties params - These will be read by ForestCanopy_data
    avg=zeros(npatch,1);
    avgH=zeros(npatch,1);
    sig=zeros(npatch,1);
    sigH=zeros(npatch,1);
    avgF=zeros(npatch,1);
    sigF=zeros(npatch,1); 
    avgAlb=zeros(npatch,1);
    sigAlb=zeros(npatch,1);
    avgBowen=zeros(npatch,1);
    sigBowen=zeros(npatch,1);
    StandDenc = zeros(npatch,1);
    HDBHpar = zeros(npatch,3);

    %Allocate canopy field variables - These are sets of fields with canopy properties per patch type. each fills the entire domains. 
    %Each field will be cut and put together according to the landscape patch. 
    % each set of fields that are associated with one patch are covarying,
    % and generated by normalization of a single, path level random filed
    % (lambdap). The canopy properties params are used for these
    % normalizations
    CSProf = zeros(npatch,101);
    LAD = zeros(npatch,101);
    AcFp = zeros(ny,nx, npatch);
    lambdap = zeros(ny,nx, npatch);
    TotLAI = zeros(ny,nx, npatch);
    Height = zeros(ny,nx, npatch);
    Bowen = zeros(ny,nx, npatch);
    TotFlux = zeros(ny,nx, npatch);
    Albedo = zeros(ny,nx, npatch);
    
%generate a random canopy field for each patch type
    for z=1:npatch
        [CSProf(z,:), HDBHpar(z,:), LAD(z,:), zcm, avg(z), avgH(z), sig(z), sigH(z), avgF(z), sigF(z), avgAlb(z), sigAlb(z), avgBowen(z), sigBowen(z), StandDenc(z),AcFp(:,:,z)] ...
            = ForestCanopy_data(patchtype(z),nx,Dx,ny,Dy);
        rand('state',sum(100*clock)); %randomize
        lambdap(:,:,z) = Make_VCaGe_rand_field(X,Y,nx,ny,Dx,Dy,AcFp(:,:,z));
   
        xvec=reshape(lambdap(:,:,z),[nx*ny 1]);
        xx=std(xvec);
        xxx=mean(xvec);
         
       %scale by mean and std
        if xx == 0
            TotLAI(:,:,z) = max(0,((lambdap(:,:,z)-xxx)+avg(z)));
            Height(:,:,z) = max(0,((lambdap(:,:,z)-xxx)+avgH(z))); 
        
            Bowen(:,:,z) = max(0,((lambdap(:,:,z)-xxx)+avgBowen(z))); 
            TotFlux(:,:,z) = max(0,((lambdap(:,:,z)-xxx)+avgF(z))); 
            Albedo(:,:,z) = max(0,((lambdap(:,:,z)-xxx)+avgAlb(z))); 
        else
            TotLAI(:,:,z) = max(0,((lambdap(:,:,z)-xxx)*(sig(z)/xx)+avg(z)));
            Height(:,:,z) = max(0,((lambdap(:,:,z)-xxx)*(sigH(z)/xx)+avgH(z))); 
        
            Bowen(:,:,z) = max(0,((lambdap(:,:,z)-xxx)*(sigBowen(z)/xx)+avgBowen(z))); 
            TotFlux(:,:,z) = max(0,((lambdap(:,:,z)-xxx)*(sigF(z)/xx)+avgF(z))); 
            Albedo(:,:,z) = max(0,((lambdap(:,:,z)-xxx)*(sigAlb(z)/xx)+avgAlb(z))); 
        end
    end
    
    %compose a combined canopy usiing landscape patch map
    TotLAIc = zeros(ny,nx);
    Heightc = zeros(ny,nx);
    
    Bowenc = zeros(ny,nx);
    TotFluxc = zeros(ny,nx);
    Albedoc = zeros(ny,nx);
    
    for xp = 1:nx
        for yp = 1:ny
            TotLAIc(yp,xp) = TotLAI(yp,xp,patch(yp,xp)); 
            Heightc(yp,xp) = Height(yp,xp,patch(yp,xp));
            Bowenc(yp,xp) = Bowen(yp,xp,patch(yp,xp));
            TotFluxc(yp,xp) = TotFlux(yp,xp,patch(yp,xp));
            Albedoc(yp,xp) = Albedo(yp,xp,patch(yp,xp));
        end
    end
else
    patch=ones(ny,nx);
    [CSProf, HDBHpar, LAD, zcm, avg, avgH, sig, sigH, avgF, sigF, avgAlb, sigAlb, avgBowen, sigBowen, StandDenc,AcFp] ...
            = ForestCanopy_data(patchtype(1),nx,Dx,ny,Dy);
    lambdap= Make_VCaGe_rand_field(X,Y,nx,ny,Dx,Dy,AcFp);
   
    xvec=reshape(lambdap,[nx*ny 1]);
    xx=std(xvec);
    xxx=mean(xvec);

    %re-scale by mean and variance
    TotLAIc = max(0,((lambdap-xxx)*(sig/xx)+avg));
    Heightc = max(0,((lambdap-xxx)*(sigH/xx)+avgH)); 
    Bowenc = max(0,((lambdap(:,:)-xxx)*(sigBowen/xx)+avgBowen)); 
    TotFluxc = max(0,((lambdap(:,:)-xxx)*(sigF/xx)+avgF)); 
    Albedoc = max(0,((lambdap(:,:)-xxx)*(sigAlb/xx)+avgAlb)); 
end
          
% place stems based on rounded coarse-grid that represents stand density.
% Puts 1 stem in each coarse-grid cell, under the tallest point in the canopy in that cell, and only if the point belong to that patch type.  
[DBHc]=Get_DBH(patch, HDBHpar, Heightc, nx,Dx, ny,Dy, StandDenc, npatch);

Hmax=max(max(Heightc));
zRi = floor(Hmax/Dz)+2; % number of vertical grid points in the canopy domain +1
dims_pzRyx=[npatch length(zcm) zRi size(TotLAIc) 0.0];

CSProf=CSProf';
LAD=LAD';
zcm = zcm';
%profiles
save ([filepath,'CSProfiles.txt'],'CSProf', '-ASCII', '-TABS'); %normalized stem cross sectional area profile
save ([filepath,'LAD.txt'], 'LAD', '-ASCII', '-TABS'); %normalized LAD profile
save ([filepath,'z.txt'], 'zcm', '-ASCII', '-TABS'); % normalized height of profiles
%maps
save ([filepath,'DBH.txt'], 'DBHc', '-ASCII', '-TABS'); % stem diameter at breast height map
save ([filepath,'TotLAI.txt'], 'TotLAIc', '-ASCII', '-TABS');
save ([filepath,'Height.txt'], 'Heightc', '-ASCII', '-TABS');
save ([filepath,'patch.txt'], 'patch', '-ASCII', '-TABS');

save ([filepath,'Ftot.txt'], 'TotFluxc', '-ASCII', '-TABS');
save ([filepath,'Bowen.txt'], 'Bowenc', '-ASCII', '-TABS');
save ([filepath,'Albedo.txt'], 'Albedoc', '-ASCII', '-TABS');

%Array size params - dims_pzRyx=[npatch length(z) zRi size(TotLAI)];
save ([filepath,'dims_pzRyx.txt'], 'dims_pzRyx', '-ASCII', '-TABS');

%Plot canopy properties
b=zeros(255,1);
r=zeros(255,1);
g=linspace(0,1,255)';
cmgreen =[r g b];
if nx*ny > 400
    figure (21)
    pcolor(X,Y,TotLAIc),xlabel('Total LAI'),colorbar,shading interp
    figure (22)
    pcolor(X,Y,Heightc),xlabel('Height'),colormap(cmgreen),colorbar,shading interp
    figure (30)
    surf(X,Y,Heightc),xlabel('Height'),colorbar,shading interp
    figure (23)
    pcolor(X,Y,patch),xlabel('Patch Type'),colorbar,shading interp
    figure (24)
    pcolor(X,Y,DBHc),xlabel('Diameter at Breast Height'),colorbar,shading interp
else
    figure (21)
    pcolor(X,Y,TotLAIc),xlabel('Total LAI'),colorbar
    figure (22)
    pcolor(X,Y,Heightc),xlabel('Height'),colorbar
    figure (23)
    pcolor(X,Y,patch),xlabel('Patch Type'),colorbar
    figure (25)
    pcolor(X,Y,DBHc),xlabel('Diameter at Breast Height'),colorbar
end

  

  