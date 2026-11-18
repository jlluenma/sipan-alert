"""Reentrenamiento manual: python scripts/train_candidate.py <directorio_version>.

Mantiene el modelo vigente. Solo usa entrenamiento.csv para ajustar el candidato;
evaluacion.csv queda reservada para comparar ambos modelos.
"""
from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import joblib
import pandas as pd
from sklearn.metrics import precision_recall_fscore_support
from sipan import config
from sipan.model import build_pipeline, load_model, hash_path_for, sha256_of
from sipan.preprocessing import normalize_for_model


def prepare(base, train, evaluation):
    for frame, partition in ((train, 'entrenamiento'), (evaluation, 'evaluacion')):
        required = {'mensaje', 'grupo_similitud', 'revision', 'particion', *config.LABELS}
        if not required.issubset(frame.columns) or frame.empty:
            raise ValueError('Se requieren particiones no vacías y con todas sus columnas.')
        if not frame.revision.eq('revisada').all() or not frame.particion.eq(partition).all():
            raise ValueError('Solo se admiten aportes revisados en su partición correspondiente.')
        if not frame[list(config.LABELS)].isin([0,1]).all().all():
            raise ValueError('Etiquetas inválidas.')
    if set(train.grupo_similitud) & set(evaluation.grupo_similitud):
        raise ValueError('Un grupo no puede aparecer en entrenamiento y evaluación.')
    train = pd.concat([base, train], ignore_index=True)
    train['_normalized'] = train.mensaje.map(normalize_for_model)
    evaluation = evaluation.copy()
    evaluation['_normalized'] = evaluation.mensaje.map(normalize_for_model)
    if set(train._normalized) & set(evaluation._normalized):
        raise ValueError('Hay mensajes duplicados entre entrenamiento y evaluación.')
    if train.groupby('_normalized')[list(config.LABELS)].nunique().gt(1).any().any():
        raise ValueError('Hay duplicados con etiquetas contradictorias; requieren revisión.')
    return train.drop_duplicates('_normalized'), evaluation.drop_duplicates('_normalized')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('version',type=Path)
    args=parser.parse_args()
    baseline=load_model()
    base=pd.read_csv(config.DATASET_PATH)
    base=base[base.revision!='descartada']
    train,test=prepare(base,pd.read_csv(args.version/'entrenamiento.csv'),pd.read_csv(args.version/'evaluacion.csv'))
    pipeline=build_pipeline().fit(train.mensaje,train[list(config.LABELS)])
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    target=config.PRIVATE_DATA_DIR/'model_candidates'/stamp
    target.mkdir(parents=True,exist_ok=False)
    model=target/'model.joblib'
    joblib.dump({'pipeline':pipeline,'labels':list(config.LABELS),'thresholds':{'signal':baseline.signal_thresholds,'review':baseline.review_thresholds},'version':'candidate_'+stamp,'trained_at':stamp,'dataset_sha256':sha256_of(args.version/'entrenamiento.csv')},model)
    hash_path_for(model).write_text(sha256_of(model),encoding='utf-8')
    def metrics(probs):
        pred=probs >= [baseline.signal_thresholds[label] for label in config.LABELS]
        p,r,f,_=precision_recall_fscore_support(test[list(config.LABELS)],pred,average='macro',zero_division=0)
        return dict(precision=float(p),recall=float(r),f1=float(f))
    report={'status':'pendiente_aprobacion','model':str(model),'training_rows':len(train),'evaluation_rows':len(test),'baseline':metrics(baseline.pipeline.predict_proba(test.mensaje)),'candidate':metrics(pipeline.predict_proba(test.mensaje)),'sources':{str(path):sha256_of(path) for path in [config.DATASET_PATH,args.version/'entrenamiento.csv',args.version/'evaluacion.csv']},'limitations':'Comparación sobre evaluación reservada de aportes nuevos. No demuestra ausencia de olvido en datos históricos. No publicar sin revisar métricas por etiqueta y un conjunto histórico independiente.'}
    (target/'evaluation.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(report,indent=2,ensure_ascii=False))


if __name__=='__main__': main()
