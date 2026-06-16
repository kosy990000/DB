# 생물정보학 지식그래프 DB 파이프라인 환경
# build:  docker build -t db .
# run:    docker run --rm -it -v $PWD:/work db
#
# environment.yml(conda env: DB)을 그대로 설치한다.
FROM mambaorg/micromamba:1.5.8

# conda 환경 생성 (environment.yml 기반)
COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml
RUN micromamba install -y -n base -f /tmp/environment.yml && \
    micromamba clean --all --yes

# 이후 RUN/CMD가 conda 환경 안에서 실행되도록
ARG MAMBA_DOCKERFILE_ACTIVATE=1

# 파이프라인 코드 복사
WORKDIR /work
COPY --chown=$MAMBA_USER:$MAMBA_USER 1_download/ /work/1_download/
COPY --chown=$MAMBA_USER:$MAMBA_USER 2_process/ /work/2_process/
COPY --chown=$MAMBA_USER:$MAMBA_USER 3_load/ /work/3_load/
COPY --chown=$MAMBA_USER:$MAMBA_USER config.yaml paths.py pipeline_lib.py run_pipeline.py /work/

# 파이썬 의존성 import 확인 (빌드 시 검증)
RUN python -c "import pandas, numpy, networkx, requests, tqdm, yaml; print('py deps OK')"

CMD ["/bin/bash"]
